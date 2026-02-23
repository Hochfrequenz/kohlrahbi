"""
Command line interface for the changehistory commands.
"""

import asyncio
from pathlib import Path

import click
from efoli import EdifactFormatVersion

from kohlrahbi.ahb.command import check_python_version, validate_path
from kohlrahbi.changehistory import scrape_change_histories
from kohlrahbi.changehistory.bnetza import download_pdfs


@click.group()
def changehistory() -> None:
    """Scrape change histories from EDIFACT documents."""


@changehistory.command()
@click.option(
    "-eemp",
    "--edi-energy-mirror-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True, path_type=Path),
    help="The root path to the edi_energy_mirror repository.",
    required=True,
)
@click.option(
    "-o",
    "--output-path",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True, path_type=Path),
    callback=validate_path,
    default="output",
    prompt="Output directory",
    help="Define the path where you want to save the generated files.",
)
@click.option(
    "--format-version",
    multiple=False,
    type=click.Choice([e.value for e in EdifactFormatVersion], case_sensitive=False),
    help="Format version(s) of the AHB documents, e.g. FV2310",
)
@click.option(
    "--assume-yes",
    "-y",
    is_flag=True,
    default=False,
    help="Confirm all prompts automatically.",
)
def docx(
    edi_energy_mirror_path: Path,
    output_path: Path,
    format_version: EdifactFormatVersion | str,
    assume_yes: bool,
) -> None:
    """Scrape change histories from .docx files in the edi_energy_mirror repository."""
    check_python_version()
    if isinstance(format_version, str):
        format_version = EdifactFormatVersion(format_version)
    input_path = edi_energy_mirror_path / "edi_energy_de"
    scrape_change_histories(input_path=input_path, output_path=output_path, format_version=format_version)


@changehistory.command()
@click.option(
    "--url",
    type=str,
    required=True,
    help="The BNetzA URL to scrape for PDF documents.",
)
@click.option(
    "-o",
    "--output-path",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True, path_type=Path),
    callback=validate_path,
    default="output",
    prompt="Output directory",
    help="Define the path where you want to save the downloaded PDFs and generated Excel file.",
)
def bnetza(url: str, output_path: Path) -> None:
    """Download PDFs from a BNetzA URL and extract change histories."""
    check_python_version()
    pdf_dir = output_path / "pdfs"
    asyncio.run(download_pdfs(url=url, target_dir=pdf_dir))
