import sys
from pathlib import Path
from typing import Literal

import click
from maus.edifact import EdifactFormatVersion

from kohlrahbi.pruefis import scrape_pruefis


def check_python_version():
    """
    Check if the Python interpreter is greater or equal to 3.11
    """
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        raise click.Abort(
            f"""Python >=3.11 is required to run this script but you use Python
{sys.version_info.major}.{sys.version_info.minor}"""
        )


def validate_path(ctx, param, value):
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
def pruefi(
    pruefis: list[str],
    input_path: Path,
    output_path: Path,
    file_type: Literal["flatahb", "csv", "xlsx"],
    format_version: EdifactFormatVersion | str,
    assume_yes: bool,  # pylint: disable=unused-argument, it is used by the callback function of the output-path
):
    check_python_version()
    if isinstance(format_version, str):
        format_version = EdifactFormatVersion(format_version)

    pruefi_to_file_mapping: dict[str, str | None] = {
        key: None for key in pruefis
    }  # A mapping of a pruefi (key) to the name (+ path) of the file containing the pruefi

    scrape_pruefis(
        pruefi_to_file_mapping=pruefi_to_file_mapping,
        basic_input_path=input_path,
        output_path=output_path,
        file_type=file_type,
        format_version=format_version,
    )
