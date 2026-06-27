#!/usr/bin/env python3
"""Safely evaluate HCL expressions with `terraform`/`tofu console`.

Hardened model (see SECURITY notes inline):
- The engine + version are validated against pre-installed binaries; nothing
  user-supplied is ever passed to a shell.
- Only `locals` blocks and bare console expressions are accepted — providers,
  resources, data sources, modules and backends are rejected, so `init` never
  downloads plugins and never touches the network.
- Each run is wrapped in a wall-clock timeout plus CPU/file/process rlimits.
"""

import json
import os
import re
import resource
import shutil
import subprocess
import uuid

SCRATCH_DIR = os.environ.get("HCL_SCRATCH_DIR", "/scratch")

# Pre-installed engine versions live here (baked into the image). The presence of
# the binary IS the allowlist — we never run a version that isn't on disk.
ENGINES = {
    "terraform": {"root": "/opt/tfenv/versions", "bin": "terraform"},
    "tofu": {"root": "/opt/tofuenv/versions", "bin": "tofu"},
}

_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Block types that would pull providers, hit the network, or read state/files.
# Matches a top-level block opener like `provider "aws" {` but not an expression
# such as `data = local.x` (assignments contain `=` before the brace).
_DISALLOWED_BLOCK_RE = re.compile(
    r"(?m)^\s*(provider|resource|data|module|terraform|backend|output|variable|"
    r"import|check|moved|removed|ephemeral)\b[^\n=]*\{"
)

# Filesystem-reading functions — `file("/etc/passwd")` et al. would leak container
# files even with no network. HCL can't alias functions, so the literal name must
# appear; a denylist is robust. (abspath/dirname/basename are string-only, allowed.)
_DISALLOWED_FUNC_RE = re.compile(r"\b(file\w*|templatefile)\s*\(")

MAX_CODE_BYTES = 64 * 1024
_TIMEOUT_SECONDS = 12


class EvaluationError(ValueError):
    """Raised for invalid/disallowed input — surfaced to the user as a 400."""


def extract_locals_blocks(text):
    """Extract all top-level ``locals { ... }`` blocks from HCL text.

    Returns ``(joined_locals_blocks, rest_of_text)``. Brace-matched so nested
    blocks are handled. (Unchanged behavior — covered by tests.)
    """
    locals_blocks = []
    rest_of_text = text
    start_pattern = re.compile(r"locals\s*{")

    while True:
        start_match = start_pattern.search(rest_of_text)
        if not start_match:
            break

        start_index = start_match.start()
        brace_count = 1
        i = start_match.end()
        while i < len(rest_of_text) and brace_count > 0:
            if rest_of_text[i] == "{":
                brace_count += 1
            elif rest_of_text[i] == "}":
                brace_count -= 1
            i += 1

        locals_blocks.append(rest_of_text[start_index:i])
        rest_of_text = rest_of_text[:start_index] + rest_of_text[i:]

    rest_of_text = "\n".join(
        line for line in rest_of_text.splitlines() if not line.startswith("//")
    )
    return "\n".join(locals_blocks), rest_of_text


def resolve_binary(engine, version):
    """Map a validated (engine, version) to a pre-installed binary path.

    Raises EvaluationError if the engine is unknown, the version isn't a strict
    semver, or that version isn't installed in the image.
    """
    if engine not in ENGINES:
        raise EvaluationError("Unknown engine (expected 'terraform' or 'tofu').")
    if not _VERSION_RE.match(version or ""):
        raise EvaluationError("Invalid version (expected e.g. 1.9.0).")
    cfg = ENGINES[engine]
    path = os.path.join(cfg["root"], version, cfg["bin"])
    # Defense-in-depth: ensure the resolved path stays under the engine root.
    if os.path.commonpath([os.path.realpath(path), cfg["root"]]) != cfg["root"]:
        raise EvaluationError("Invalid version.")
    if not os.path.isfile(path):
        raise EvaluationError("That version isn't available.")
    return path


def installed_versions(engine):
    """Versions actually installed in the image for an engine, newest first.

    This is the dropdown's source of truth — no network, and it can only ever
    offer versions that ``resolve_binary`` will accept.
    """
    cfg = ENGINES.get(engine)
    if not cfg:
        return []
    try:
        names = os.listdir(cfg["root"])
    except OSError:
        return []
    versions = [
        name
        for name in names
        if _VERSION_RE.match(name)
        and os.path.isfile(os.path.join(cfg["root"], name, cfg["bin"]))
    ]
    return sorted(versions, key=lambda v: [int(p) for p in v.split(".")], reverse=True)


def _validate_code(code):
    if code is None:
        raise EvaluationError("No code provided.")
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        raise EvaluationError("Input too large.")
    if _DISALLOWED_BLOCK_RE.search(code):
        raise EvaluationError(
            "Only `locals` blocks and console expressions are allowed — "
            "providers, resources, data sources, modules and backends are not."
        )
    if _DISALLOWED_FUNC_RE.search(code):
        raise EvaluationError(
            "Filesystem functions (file(), templatefile(), fileset(), ...) "
            "aren't allowed."
        )


def _set_limits():
    """Child-process rlimits (runs in the forked child before exec).

    NB: we intentionally do NOT set RLIMIT_AS — Go binaries reserve huge virtual
    address space and would be killed. Memory is bounded by the container/cgroup
    limit instead. Here we cap CPU time, output file size, and process count.
    """
    resource.setrlimit(resource.RLIMIT_CPU, (_TIMEOUT_SECONDS, _TIMEOUT_SECONDS))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024 * 1024, 16 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))


def _run(args, workdir, stdin=None, tf_cli_args=True):
    """Run a binary with no shell, a curated env, rlimits, and a hard timeout."""
    env = {
        "HOME": workdir,
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "TF_IN_AUTOMATION": "1",
        "TF_INPUT": "0",
        "CHECKPOINT_DISABLE": "1",  # no version-check phone-home
        "NO_COLOR": "1",
    }
    if tf_cli_args:
        # Appended to every command — fine for init/console, but `metadata
        # functions` rejects unknown flags, so callers can opt out.
        env["TF_CLI_ARGS"] = "-no-color"
    return subprocess.run(
        args,
        cwd=workdir,
        input=stdin,
        env=env,
        shell=False,
        check=False,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        preexec_fn=_set_limits,
    )


def evaluate(engine, version, code):
    """Validate, then evaluate ``code`` offline via ``<engine> console``.

    Returns the combined console stdout/stderr (string). Raises EvaluationError
    for bad input.
    """
    _validate_code(code)
    binary = resolve_binary(engine, version)
    locals_block, expression = extract_locals_blocks(code)

    run_id = uuid.uuid4().hex
    workdir = os.path.join(SCRATCH_DIR, run_id)
    os.makedirs(workdir)
    try:
        if locals_block.strip():
            with open(os.path.join(workdir, "main.tf"), "w") as fh:
                fh.write(locals_block)

        # Offline init: no providers are allowed, so nothing is downloaded.
        init = _run(
            [binary, "init", "-backend=false", "-input=false", "-no-color"], workdir
        )
        if init.returncode != 0:
            return (init.stdout or "") + (init.stderr or "")

        console = _run([binary, "console"], workdir, stdin=expression)
        return (console.stdout or "") + (console.stderr or "")
    except subprocess.TimeoutExpired:
        return "Error: evaluation timed out."
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


_FUNCTIONS_CACHE = {}


def list_functions(engine, version):
    """The engine's own function catalog for (engine, version), for autocomplete.

    Sourced from `<engine> metadata functions -json` so it's exactly right for
    that binary (functions differ across versions and between TF/OpenTofu).
    Cached — the catalog is static per binary. Returns [{name, sig, doc}].
    """
    binary = resolve_binary(engine, version)  # validates engine + version
    key = (engine, version)
    if key in _FUNCTIONS_CACHE:
        return _FUNCTIONS_CACHE[key]

    result = _run([binary, "metadata", "functions", "-json"], SCRATCH_DIR, tf_cli_args=False)
    functions = []
    if result.returncode == 0:
        try:
            signatures = json.loads(result.stdout).get("function_signatures") or {}
        except ValueError:
            signatures = {}
        for name, sig in sorted(signatures.items()):
            if "::" in name:
                continue  # skip namespaced duplicates like core::abs / provider::
            functions.append(
                {"name": name, "sig": _format_signature(name, sig), "doc": _short_doc(sig)}
            )
    _FUNCTIONS_CACHE[key] = functions
    return functions


def _format_signature(name, sig):
    params = [p.get("name", "") for p in (sig.get("parameters") or [])]
    variadic = sig.get("variadic_parameter")
    if variadic:
        params.append((variadic.get("name", "") or "arg") + "...")
    return "{}({})".format(name, ", ".join(params))


def _short_doc(sig):
    desc = (sig.get("description") or "").replace("`", "").strip()
    # descriptions are markdown; first sentence/line is enough for a tooltip.
    for stop in (". ", "\n"):
        idx = desc.find(stop)
        if idx != -1:
            desc = desc[: idx + (1 if stop == ". " else 0)]
            break
    return desc[:160]
