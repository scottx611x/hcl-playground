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

import hashlib
import io
import json
import os
import platform
import re
import resource
import shutil
import subprocess
import threading
import time
import urllib.request
import uuid
import zipfile

SCRATCH_DIR = os.environ.get("HCL_SCRATCH_DIR", "/scratch")

# Versions can live in two places: baked into the image (read-only) and a writable
# runtime dir (works on read-only deploys like Lambda, where only /tmp is writable).
RUNTIME_ROOT = os.environ.get("HCL_RUNTIME_ROOT", "/tmp/hcl-engines")

# Optional S3 cache: persists on-demand-installed binaries so they survive cold
# starts / new containers (set HCL_CACHE_BUCKET to enable).
CACHE_BUCKET = os.environ.get("HCL_CACHE_BUCKET")

ENGINES = {
    "terraform": {"baked": "/opt/tfenv/versions", "bin": "terraform"},
    "tofu": {"baked": "/opt/tofuenv/versions", "bin": "tofu"},
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


_INSTALL_LOCK = threading.Lock()

# Frozen mode (set HCL_FROZEN=1) disables on-demand installs entirely.
ALLOW_INSTALL = os.environ.get("HCL_FROZEN") != "1"


def _arch():
    machine = platform.machine().lower()
    return "arm64" if machine in ("aarch64", "arm64") else "amd64"


def _roots(engine):
    """Where an engine's versions may live: baked (read-only) + writable runtime."""
    return [ENGINES[engine]["baked"], os.path.join(RUNTIME_ROOT, engine)]


def _binary_path(engine, version):
    """Existing binary path for (engine, version), across baked + runtime roots."""
    binary = ENGINES[engine]["bin"]
    for root in _roots(engine):
        path = os.path.join(root, version, binary)
        if os.path.isfile(path):
            return path
    return None


def _download_spec(engine, version):
    """(`zip_url`, `sums_url`, `zip_name`) for an official release."""
    arch = _arch()
    if engine == "terraform":
        base = "https://releases.hashicorp.com/terraform/{v}".format(v=version)
        name = "terraform_{v}_linux_{a}.zip".format(v=version, a=arch)
        return base + "/" + name, base + "/terraform_{v}_SHA256SUMS".format(v=version), name
    base = "https://github.com/opentofu/opentofu/releases/download/v{v}".format(v=version)
    name = "tofu_{v}_linux_{a}.zip".format(v=version, a=arch)
    return base + "/" + name, base + "/tofu_{v}_SHA256SUMS".format(v=version), name


def _http_get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "hcl-playground"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _cache_key(engine, version):
    return "engines/{e}/{v}/{a}/{b}".format(
        e=engine, v=version, a=_arch(), b=ENGINES[engine]["bin"]
    )


def _cache_fetch(engine, version, dest):
    if not CACHE_BUCKET:
        return False
    try:
        import boto3

        boto3.client("s3").download_file(CACHE_BUCKET, _cache_key(engine, version), dest)
        return True
    except Exception:  # noqa: BLE001 - miss / unavailable -> fall through to download
        return False


def _cache_store(engine, version, src):
    if not CACHE_BUCKET:
        return
    try:
        import boto3

        boto3.client("s3").upload_file(src, CACHE_BUCKET, _cache_key(engine, version))
    except Exception:  # noqa: BLE001 - caching is best-effort
        pass


def _download_and_verify(engine, version, dest):
    """Download the official release zip, verify its SHA-256, extract the binary."""
    zip_url, sums_url, zip_name = _download_spec(engine, version)
    try:
        archive = _http_get(zip_url)
        sums = _http_get(sums_url).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        raise EvaluationError(
            "Couldn't download {} {} — is it a real release?".format(engine, version)
        )
    expected = None
    for line in sums.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == zip_name:
            expected = parts[0].lower()
            break
    if not expected:
        raise EvaluationError("No checksum found for {} {}.".format(engine, version))
    if hashlib.sha256(archive).hexdigest().lower() != expected:
        raise EvaluationError("Checksum mismatch for {} {}.".format(engine, version))
    binary = ENGINES[engine]["bin"]
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        with zf.open(binary) as src, open(dest, "wb") as out:
            shutil.copyfileobj(src, out)


def ensure_installed(engine, version):
    """Make sure (engine, version) is available, pulling it on demand if not.

    Resolution order: baked image -> writable runtime dir -> S3 cache -> official
    download (checksum-verified) which is then cached to S3. Returns the path.
    """
    if engine not in ENGINES:
        raise EvaluationError("Unknown engine (expected 'terraform' or 'tofu').")
    if not _VERSION_RE.match(version or ""):
        raise EvaluationError("Invalid version (expected e.g. 1.10.5).")
    path = _binary_path(engine, version)
    if path:
        return path
    if not ALLOW_INSTALL:
        raise EvaluationError("That version isn't available here.")

    dest_dir = os.path.join(RUNTIME_ROOT, engine, version)
    dest = os.path.join(dest_dir, ENGINES[engine]["bin"])
    with _INSTALL_LOCK:
        path = _binary_path(engine, version)  # installed while we waited
        if path:
            return path
        os.makedirs(dest_dir, exist_ok=True)
        if not _cache_fetch(engine, version, dest):
            _download_and_verify(engine, version, dest)
            _cache_store(engine, version, dest)
        os.chmod(dest, 0o755)
    return dest


def resolve_binary(engine, version):
    """Path to an already-available (engine, version) binary, or raise."""
    if engine not in ENGINES:
        raise EvaluationError("Unknown engine (expected 'terraform' or 'tofu').")
    if not _VERSION_RE.match(version or ""):
        raise EvaluationError("Invalid version (expected e.g. 1.9.0).")
    path = _binary_path(engine, version)
    if not path:
        raise EvaluationError("That version isn't available.")
    return path


_AVAILABLE_CACHE = {}  # engine -> (timestamp, [versions])
_AVAILABLE_TTL = 3600


def available_versions(engine, limit=30):
    """Installable versions from the engine's official release feed (cached)."""
    cached = _AVAILABLE_CACHE.get(engine)
    if cached and time.time() - cached[0] < _AVAILABLE_TTL:
        return cached[1]
    versions = _fetch_available(engine)[:limit]
    if versions:
        _AVAILABLE_CACHE[engine] = (time.time(), versions)
    return versions


def _fetch_available(engine):
    try:
        if engine == "terraform":
            data = json.loads(_http_get("https://releases.hashicorp.com/terraform/index.json", 15))
            names = data.get("versions", {}).keys()
        elif engine == "tofu":
            # Tags are far lighter than the releases API (no changelog/asset bodies).
            data = json.loads(_http_get("https://api.github.com/repos/opentofu/opentofu/tags?per_page=100", 15))
            names = [(t.get("name") or "").lstrip("v") for t in data]
        else:
            return []
    except Exception:  # noqa: BLE001 - feed unavailable -> just offer what's installed
        return []
    stable = [v for v in names if _VERSION_RE.match(v)]
    return sorted(stable, key=lambda v: [int(p) for p in v.split(".")], reverse=True)


def installed_versions(engine):
    """Versions currently on disk for an engine (baked + runtime), newest first."""
    if engine not in ENGINES:
        return []
    binary = ENGINES[engine]["bin"]
    found = set()
    for root in _roots(engine):
        try:
            names = os.listdir(root)
        except OSError:
            continue
        for name in names:
            if _VERSION_RE.match(name) and os.path.isfile(os.path.join(root, name, binary)):
                found.add(name)
    return sorted(found, key=lambda v: [int(p) for p in v.split(".")], reverse=True)


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
    ensure_installed(engine, version)
    binary = resolve_binary(engine, version)
    locals_block, expression = extract_locals_blocks(code)
    expression = expression.strip()

    run_id = uuid.uuid4().hex
    workdir = os.path.join(SCRATCH_DIR, run_id)
    os.makedirs(workdir)
    try:
        # Write the user's locals plus the trailing expression wrapped as a local
        # value. `console` then evaluates a single-line reference, which sidesteps
        # its line-by-line stdin parsing — a multi-line expression piped directly
        # otherwise fails with "Missing expression".
        main_tf = locals_block or ""
        if expression:
            main_tf += "\n\nlocals {\n  _hclpg_result = (\n" + expression + "\n  )\n}\n"
        if main_tf.strip():
            with open(os.path.join(workdir, "main.tf"), "w") as fh:
                fh.write(main_tf)

        # Offline init: no providers are allowed, so nothing is downloaded.
        init = _run(
            [binary, "init", "-backend=false", "-input=false", "-no-color"], workdir
        )
        if init.returncode != 0:
            return (init.stdout or "") + (init.stderr or "")

        if not expression:
            return "Add an expression (outside any locals block) to evaluate."

        console = _run([binary, "console"], workdir, stdin="local._hclpg_result\n")
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
    key = (engine, version)
    if key in _FUNCTIONS_CACHE:
        return _FUNCTIONS_CACHE[key]
    ensure_installed(engine, version)
    binary = resolve_binary(engine, version)  # validates engine + version

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
