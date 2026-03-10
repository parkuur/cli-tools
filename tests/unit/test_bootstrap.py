"""Basic repository bootstrap sanity tests."""

# Tests intentionally use short test functions and may rely on pytest import
# patterns. Disable pylint checks for import placement and function docstrings
# to keep tests concise while addressing module docstring requirements.
# pylint: disable=import-outside-toplevel,missing-function-docstring

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_src_directories_exist() -> None:
    base = Path.cwd()
    assert (base / "src" / "core_lib").exists(), "src/core_lib must exist"
    assert (base / "src" / "cli_layer").exists(), "src/cli_layer must exist"


def test_support_dirs_and_files_exist() -> None:
    base = Path.cwd()
    assert (base / "tests").exists(), "tests/ directory must exist"
    assert (base / "scripts").exists(), "scripts/ directory must exist"
    assert (base / "pyproject.toml").exists(), "pyproject.toml must exist"
    assert (base / "README.md").exists(), "README.md must exist"
    assert (base / ".gitignore").exists(), ".gitignore must exist"


def test_init_files_exist_for_packages() -> None:
    base = Path.cwd()
    assert (base / "src" / "core_lib" / "__init__.py").exists(), (
        "src/core_lib/__init__.py must exist"
    )
    assert (base / "src" / "cli_layer" / "__init__.py").exists(), (
        "src/cli_layer/__init__.py must exist"
    )
