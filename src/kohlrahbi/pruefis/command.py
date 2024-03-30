from pathlib import Path
from typing import Literal

import click
from maus.edifact import EdifactFormatVersion


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
    file_type: Literal["flatahb", "csv", "xlsx", "conditions"],
    format_version: EdifactFormatVersion | str,
    assume_yes: bool,
):
    pass
