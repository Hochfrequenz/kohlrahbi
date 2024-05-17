"""
Command line interface for the changehistory command.
"""

from pathlib import Path

import click
from maus.edifact import EdifactFormatVersion

from kohlrahbi.ahb.command import check_python_version, validate_path
from kohlrahbi.changehistory import scrape_change_histories


@click.command()
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
def changehistory(
    edi_energy_mirror_path: Path,
    output_path: Path,
    format_version: EdifactFormatVersion | str,
    assume_yes: bool,  # pylint: disable=unused-argument
    # it is used by the callback function of the output-path
) -> None:
    """
    Scrape change histories from the input path and save them to the output path.

    Args:
        edi_energy_mirror_path (Path): The path to the input file or directory containing change histories.
        output_path (Path): The path to save the scraped change histories.
        format_version (EdifactFormatVersion | str): The version of the EDIFACT format to use for scraping.
            Can be either an instance of EdifactFormatVersion or a string representation of the version.
        assume_yes (bool): Flag indicating whether to assume "yes" for all prompts.
    """
    check_python_version()
    if isinstance(format_version, str):
        format_version = EdifactFormatVersion(format_version)
    input_path = edi_energy_mirror_path / "edi_energy_de" / format_version.value
    scrape_change_histories(input_path=input_path, output_path=output_path)
