"""Tests for the changehistory docx CLI subcommand."""

from pathlib import Path

from typer.testing import CliRunner

from kohlrahbi import app

runner = CliRunner()


def test_changehistory_docx_subcommand(tmp_path: Path) -> None:
    """changehistory docx should scrape change histories and write an xlsx file."""
    output_path = tmp_path / "output"
    result = runner.invoke(
        app,
        [
            "changehistory",
            "docx",
            "--edi-energy-mirror-path",
            str(Path(__file__).parents[1] / "edi_energy_mirror"),
            "--output-path",
            str(output_path),
            "--format-version",
            "FV2310",
            "--assume-yes",
        ],
    )
    assert result.exit_code == 0, result.output
    xlsx_files = list(output_path.glob("*_change_histories.xlsx"))
    assert len(xlsx_files) == 1
