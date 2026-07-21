"""Tests for the shared CLI helpers in kohlrahbi.cli_utils."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import typer
from rich.console import Console

from kohlrahbi.cli_utils import check_python_version, ensure_output_path


def test_check_python_version_raises_below_3_11(monkeypatch: pytest.MonkeyPatch) -> None:
    """check_python_version should exit if the interpreter is older than 3.11."""
    monkeypatch.setattr(sys, "version_info", SimpleNamespace(major=3, minor=10))
    with pytest.raises(typer.Exit):
        check_python_version(Console())


def test_check_python_version_passes_on_3_11(monkeypatch: pytest.MonkeyPatch) -> None:
    """check_python_version should not raise for a supported interpreter."""
    monkeypatch.setattr(sys, "version_info", SimpleNamespace(major=3, minor=11))
    check_python_version(Console())


def test_ensure_output_path_creates_dir_when_assume_yes(tmp_path: Path) -> None:
    """ensure_output_path should create the directory when assume_yes is True."""
    output_path = tmp_path / "does-not-exist-yet"
    result = ensure_output_path(Console(), output_path, assume_yes=True)
    assert result == output_path
    assert output_path.exists()


def test_ensure_output_path_exits_when_user_declines(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ensure_output_path should exit without creating the directory if the user declines."""
    output_path = tmp_path / "declined"
    monkeypatch.setattr(typer, "confirm", lambda *_args, **_kwargs: False)
    with pytest.raises(typer.Exit):
        ensure_output_path(Console(), output_path, assume_yes=False)
    assert not output_path.exists()
