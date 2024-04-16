import pytest
from backend.terraform_utils import extract_locals_block  # Adjust the import according to your project structure

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
    locals_block, rest = extract_locals_block(hcl_text)
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
    locals_block, rest = extract_locals_block(hcl_text)
    assert locals_block is None
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
    locals_block, rest = extract_locals_block(hcl_text)
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
    locals_block, rest = extract_locals_block(hcl_text)
    assert locals_block.strip() == '''locals {
      name = "with-comment"
      // another comment inside
    }'''.strip()
    assert 'name = "with-comment"' not in rest
    assert "// This is a comment" in rest
    assert "// Final comment" in rest
    assert "// another comment inside" not in rest