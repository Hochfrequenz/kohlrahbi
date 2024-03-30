"""
kohlrahbi is a package to scrape AHBs (in docx format)
"""

import sys
from pathlib import Path
from typing import Literal

import click
from maus.edifact import EdifactFormatVersion

from kohlrahbi.changehistory.command import changehistory
from kohlrahbi.changehistory.functions import scrape_change_histories
from kohlrahbi.conditions.command import conditions
from kohlrahbi.logger import logger
from kohlrahbi.pruefis import scrape_pruefis
from kohlrahbi.pruefis.command import pruefi, validate_path


def check_python_version():
    """
    Check if the Python interpreter is greater or equal to 3.11
    """
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        raise click.Abort(
            f"""Python >=3.11 is required to run this script but you use Python
{sys.version_info.major}.{sys.version_info.minor}"""
        )


@click.command()
@click.option(
    "-f",
    "--flavour",
    type=click.Choice(["pruefi", "changehistory"], case_sensitive=False),
    default="pruefi",
    help='Choose between "pruefi" and "changehistory".',
)
@click.option(
    "-p",
    "--pruefis",
    default=[],
    required=False,
    help="Five digit number like 11042 or use wildcards like 110* or *042 or 11?42.",
    multiple=True,
)
@click.option(
    "-i",
    "--input-path",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    prompt="Input directory",
    help="Define the path to the folder with the docx AHBs.",
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
    "--file-type",
    type=click.Choice(["flatahb", "csv", "xlsx", "conditions"], case_sensitive=False),
    multiple=True,
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
# pylint: disable=too-many-arguments
def main(
    flavour: str,
    pruefis: list[str],
    input_path: Path,
    output_path: Path,
    file_type: Literal["flatahb", "csv", "xlsx", "conditions"],
    format_version: EdifactFormatVersion | str,
    assume_yes: bool,
) -> None:
    """
    A program to get a machine readable version of the AHBs docx files published by edi@energy.
    """
    check_python_version()
    if isinstance(format_version, str):
        format_version = EdifactFormatVersion(format_version)

    pruefi_to_file_mapping: dict[str, str | None] = {
        key: None for key in pruefis
    }  # A mapping of a pruefi (key) to the name (+ path) of the file containing the prufi
    match flavour:
        case "changehistory":
            scrape_change_histories(input_path=input_path, output_path=output_path)


@click.group()
def cli():
    """Kohlrahbi CLI tool"""


# Add commands to the CLI group
cli.add_command(pruefi)
cli.add_command(changehistory)
cli.add_command(conditions)

if __name__ == "__main__":
    # the parameter arguments gets provided over the CLI
    cli()  # pylint:disable=no-value-for-parameter
