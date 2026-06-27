import inspect

import pytest

from backend import terraform_utils
from backend.terraform_utils import (
    EvaluationError,
    _validate_code,
    extract_locals_blocks,
    resolve_binary,
)


# ---------------------------------------------------------------------------
# Security: engine/version validation (command-injection prevention)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "engine,version",
    [
        ("terraform", "1.0.0; rm -rf /"),   # shell injection attempt
        ("terraform", "$(curl evil)"),
        ("terraform", "../../etc/passwd"),  # path traversal
        ("terraform", "latest"),            # not strict semver
        ("terraform", ""),
        ("bash", "1.0.0"),                  # unknown engine
        ("terraform; id", "1.0.0"),
    ],
)
def test_resolve_binary_rejects_bad_input(engine, version):
    with pytest.raises(EvaluationError):
        resolve_binary(engine, version)


def test_resolve_binary_rejects_uninstalled_version(tmp_path, monkeypatch):
    # Valid semver but not installed -> rejected (no binary on disk).
    monkeypatch.setitem(
        terraform_utils.ENGINES, "terraform", {"baked": str(tmp_path), "bin": "terraform"}
    )
    monkeypatch.setattr(terraform_utils, "RUNTIME_ROOT", str(tmp_path / "runtime"))
    with pytest.raises(EvaluationError):
        resolve_binary("terraform", "9.9.9")


# ---------------------------------------------------------------------------
# Security: only locals blocks + expressions allowed
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "code",
    [
        'provider "aws" { region = "us-east-1" }',
        'resource "aws_instance" "x" { ami = "abc" }',
        'data "aws_ami" "x" { owners = ["self"] }',
        'module "x" { source = "./m" }',
        'terraform { backend "s3" {} }',
    ],
)
def test_validate_code_rejects_disallowed_blocks(code):
    with pytest.raises(EvaluationError):
        _validate_code(code)


@pytest.mark.parametrize(
    "code",
    [
        'file("/etc/passwd")',
        'filebase64("/etc/shadow")',
        'templatefile("x.tpl", {})',
        'fileset(path.module, "*")',
        'yamldecode(file("/secrets"))',
    ],
)
def test_validate_code_rejects_filesystem_functions(code):
    with pytest.raises(EvaluationError):
        _validate_code(code)


def test_validate_code_allows_locals_and_expressions():
    _validate_code('locals { x = 1 }\nupper("hi")')  # should not raise
    # an assignment-style expression containing "data" is fine (not a block)
    _validate_code("local.data_map")


def test_validate_code_rejects_oversized_input():
    with pytest.raises(EvaluationError):
        _validate_code("#" * (terraform_utils.MAX_CODE_BYTES + 1))


# ---------------------------------------------------------------------------
# Security: never use a shell
# ---------------------------------------------------------------------------
def test_no_shell_usage_in_subprocess_calls():
    source = inspect.getsource(terraform_utils)
    assert "shell=True" not in source
    assert "shell=False" in source  # explicit

def test_extract_locals_with_valid_block():
    hcl_text = """
    resource "aws_instance" "example" {
      ami           = "abc123"
    }

    locals {
      name = "example-instance"
      type = "t2.micro"
    }

    variable "region" {
      default = "us-west-2"
    }
    """
    locals_block, rest = extract_locals_blocks(hcl_text)
    assert locals_block.strip() == '''locals {
      name = "example-instance"
      type = "t2.micro"
    }'''.strip()
    assert 'locals {' not in rest
    assert 'name = "example-instance"' not in rest
    assert 'type = "t2.micro"' not in rest


def test_extract_locals_without_block():
    hcl_text = """
    resource "aws_instance" "example" {
      ami           = "abc123"
    }
    """
    locals_block, rest = extract_locals_blocks(hcl_text)
    assert locals_block == ""
    assert rest == hcl_text


def test_extract_locals_with_nested_blocks():
    hcl_text = """
    locals {
      nested {
        key = "value"
      }
      name = "nested-instance"
    }
    """
    locals_block, rest = extract_locals_blocks(hcl_text)
    assert locals_block.strip() == '''locals {
      nested {
        key = "value"
      }
      name = "nested-instance"
    }'''.strip()
    assert rest.strip() == ""

def test_extract_locals_with_comments():
    hcl_text = """
    // This is a comment
    locals {
      name = "with-comment"
      // another comment inside
    }
    // Final comment
    """
    locals_block, rest = extract_locals_blocks(hcl_text)
    assert locals_block.strip() == '''locals {
      name = "with-comment"
      // another comment inside
    }'''.strip()
    assert 'name = "with-comment"' not in rest
    assert "// This is a comment" in rest
    assert "// Final comment" in rest
    assert "// another comment inside" not in rest


def test_extract_all_locals_blocks():
    hcl_text = """
    locals {
      first_block = "first-value"
    }

    resource "aws_instance" "example" {
      ami = "abc123"
    }

    locals {
      second_block = "second-value"
    }
    """

    # Define the expected output as a single string
    expected = """
    locals {
      first_block = "first-value"
    }
locals {
      second_block = "second-value"
    }
    """.strip()  # .strip() to remove any leading/trailing newlines

    locals_blocks, rest = extract_locals_blocks(hcl_text)

    # Remove leading/trailing whitespace for a fair comparison
    locals_blocks = locals_blocks.strip()

    # Perform assertions
    assert locals_blocks == expected
    assert 'locals {' not in rest
    assert 'first_block = "first-value"' not in rest
    assert 'second_block = "second-value"' not in rest