"""
This module contains a command-line interface for handling conditions.

The `conditions` function is the main entry point for the command-line interface.
It takes several options as command-line arguments and performs the necessary operations based on those options.

Options:
- `--edi-energy-mirror-path`: Specifies the path to the edi_energy_mirror repository.
- `--output-path`: Specifies the path where the generated files will be saved.
- `--format-version`: Specifies the format version(s) of the AHB documents.
- `--assume-yes`: Automatically confirms all prompts.

Usage:
To use this command-line interface, run the script and provide the necessary options as command-line arguments.

Example:
$ python command.py --edi-energy-mirror-path /path/to/edi_energy_mirror/repo
 --output-path /path/to/output --format-version FV2310 --assume-yes
"""

from pathlib import Path

import click
from maus.edifact import EdifactFormatVersion

from kohlrahbi.ahb.command import validate_path


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
# pylint: disable=unused-argument
def conditions(
    input_path: Path,
    output_path: Path,
    format_version: EdifactFormatVersion | str,
    assume_yes: bool,
):
    """
    Scrape AHB documents for conditions.
    """
