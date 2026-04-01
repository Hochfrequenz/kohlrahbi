"""Tests for the changehistory CLI group and bnetza subcommand."""

from typer.testing import CliRunner

from kohlrahbi import app

runner = CliRunner()


def test_changehistory_is_a_group() -> None:
    """changehistory should be a typer group with subcommands."""
    result = runner.invoke(app, ["changehistory", "--help"])
    assert result.exit_code == 0
    assert "docx" in result.output
    assert "bnetza" in result.output


def test_bnetza_subcommand_help() -> None:
    """bnetza subcommand should accept --url option."""
    result = runner.invoke(app, ["changehistory", "bnetza", "--help"])
    assert result.exit_code == 0
    assert "--url" in result.output
