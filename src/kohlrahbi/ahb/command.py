""""
Command line interface for the pruefis module.
"""

import sys
from pathlib import Path

import click
from maus.edifact import EdifactFormatVersion

from kohlrahbi.ahb import scrape_pruefis
from kohlrahbi.enums.ahbexportfileformat import AhbExportFileFormat


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
    "-p",
    "--pruefis",
    default=[],
    required=False,
    help="Five digit number like 11042 or use wildcards like 110* or *042 or 11?42.",
    multiple=True,
)
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
    "--file-type",
    type=click.Choice([aeff.value for aeff in AhbExportFileFormat], case_sensitive=False),
    multiple=True,
    required=True,
    help="File type(s) for the scraped AHB documents.",
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
# pylint: disable=too-many-arguments
def ahb(
    pruefis: list[str],
    edi_energy_mirror_path: Path,
    output_path: Path,
    file_type: tuple[AhbExportFileFormat, ...],
    format_version: EdifactFormatVersion | str,
    assume_yes: bool,  # pylint: disable=unused-argument
    # it is used by the callback function of the output-path
) -> None:
    """
    Scrape AHB documents for pruefidentifikatoren.
    This is a command line interface for the pruefis module.
    """
    check_python_version()
    if isinstance(format_version, str):
        format_version = EdifactFormatVersion(format_version)

    scrape_pruefis(
        pruefis=list(pruefis),
        basic_input_path=edi_energy_mirror_path,
        output_path=output_path,
        file_type=file_type,
        format_version=format_version,
    )
