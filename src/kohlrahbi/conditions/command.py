"""
This module contains a command-line interface for handling conditions.

The `conditions` function is the main entry point for the command-line interface.
It takes several options as command-line arguments and performs the necessary operations based on those options.

Options:
- `--edi-energy-mirror-path`: Specifies the path to the directory with an edi_energy_mirror repository structure.
- `--output-path`: Specifies the path where the generated files will be saved.
- `--format-version`: Specifies the format version(s) of the AHB documents.
- `--assume-yes`: Automatically confirms all prompts.

Usage:
To use this command-line interface, run the script and provide the necessary options as command-line arguments.

Example:
$ python command.py --eemp /path/to/eemp --output-path /path/to/output --format-version FV2310 --assume-yes
"""

# pylint: disable=duplicate-code
# duplicate-code warning is disabled because the code cli structure of 'ahb' and 'conditions' are intentionally similar.
import sys
from pathlib import Path

import click
from maus.edifact import EdifactFormatVersion

from kohlrahbi.conditions import scrape_conditions


def check_python_version() -> None:
    """
    Check if the Python interpreter is greater or equal to 3.11
    """
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        raise click.Abort(
            f"""Python >=3.11 is required to run this script but you use Python
{sys.version_info.major}.{sys.version_info.minor}"""
        )


# pylint: disable=unused-argument
def validate_path(ctx, param, value) -> Path:  # type:ignore[no-untyped-def]
    """
    Ensure the path exists or offer to create it.
    """
    path = Path(value)
    if not path.exists():
        if ctx.params.get("assume_yes") or click.confirm(
            f"The path {value} does not exist. Would you like to create it?"
        ):
            path.mkdir(parents=True)
            click.secho(f"Created directory {path}.", fg="green")
        else:
            click.secho("👋 Alright I will end this program now. Have a nice day.", fg="green")
            raise click.Abort()
    return path


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
    help="""Define the path where you want to save the generated files. If the path does not exist,
you will be asked if you want to create it.""",
)
@click.option(
    "--format-version",
    multiple=False,
    type=click.Choice([e.value for e in EdifactFormatVersion], case_sensitive=False),
    required=True,
    help="Format version(s) of the AHB documents, e.g. FV2310",
)
@click.option(
    "--assume-yes",
    "-y",
    is_flag=True,
    default=False,
    help="Confirm all prompts automatically.",
)
def conditions(
    edi_energy_mirror_path: Path, output_path: Path, format_version: EdifactFormatVersion | str, assume_yes: bool
) -> None:
    """
    Scrape AHB documents for conditions.
    """
    check_python_version()
    if isinstance(format_version, str):
        format_version = EdifactFormatVersion(format_version)

    scrape_conditions(
        basic_input_path=edi_energy_mirror_path,
        output_path=output_path,
        format_version=format_version,
    )
