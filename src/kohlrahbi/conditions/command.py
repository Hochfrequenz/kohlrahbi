"""
Command line interface for handling conditions.
"""

# pylint: disable=import-outside-toplevel
# Heavy submodules are imported lazily inside the command functions so that `--help` stays fast.

import sys
from pathlib import Path
from typing import Annotated

import typer
from efoli import EdifactFormatVersion
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from kohlrahbi.logger import setup_logging

console = Console()

conditions_app = typer.Typer(invoke_without_command=True)


def check_python_version() -> None:
    """Check if the Python interpreter is greater or equal to 3.11"""
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        console.print("[red]Python >=3.11 is required to run this script.[/red]")
        raise typer.Exit(code=1)


@conditions_app.callback(invoke_without_command=True)
def conditions(
    edi_energy_mirror_path: Annotated[
        Path,
        typer.Option(
            "-eemp",
            "--edi-energy-mirror-path",
            help="The root path to the edi_energy_mirror repository.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = ...,  # type: ignore[assignment]
    output_path: Annotated[
        Path,
        typer.Option(
            "-o",
            "--output-path",
            help="Define the path where you want to save the generated files.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("output"),
    format_version: Annotated[
        str,
        typer.Option(
            "--format-version",
            help="Format version of the AHB documents, e.g. FV2310.",
        ),
    ] = ...,  # type: ignore[assignment]
    assume_yes: Annotated[
        bool,
        typer.Option(
            "-y",
            "--assume-yes",
            help="Confirm all prompts automatically.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "-v",
            "--verbose",
            help="Enable verbose logging output.",
        ),
    ] = False,
) -> None:
    """
    Scrape AHB documents for conditions.
    """
    setup_logging(verbose=verbose)
    check_python_version()

    from kohlrahbi.ahb.command import ensure_output_path

    output_path = ensure_output_path(output_path, assume_yes)
    efv = EdifactFormatVersion(format_version)

    from kohlrahbi.conditions import scrape_conditions

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Scraping conditions...", total=None)
        scrape_conditions(
            basic_input_path=edi_energy_mirror_path,
            output_path=output_path,
            format_version=efv,
        )

    console.print(
        Panel(
            f"[blue]Output:[/blue] {output_path}",
            title="Conditions Scraping Complete",
            border_style="green",
        )
    )
