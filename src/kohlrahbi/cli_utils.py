"""
Shared helpers for the Typer command-line entrypoints.
"""

import sys
from pathlib import Path

import typer
from efoli import EdifactFormatVersion
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from kohlrahbi.logger import setup_logging


def check_python_version(console: Console) -> None:
    """Check if the Python interpreter is greater or equal to 3.11."""
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        console.print("[red]Python >=3.11 is required to run this script.[/red]")
        raise typer.Exit(code=1)


def ensure_output_path(console: Console, output_path: Path, assume_yes: bool) -> Path:
    """Ensure the output path exists or offer to create it."""
    if not output_path.exists():
        if assume_yes or typer.confirm(f"The path {output_path} does not exist. Would you like to create it?"):
            output_path.mkdir(parents=True)
            console.print(f"[green]Created directory {output_path}.[/green]")
        else:
            console.print("[green]Alright, exiting. Have a nice day.[/green]")
            raise typer.Exit()
    return output_path


def prepare_command(
    *,
    console: Console,
    verbose: bool,
    output_path: Path,
    assume_yes: bool,
    format_version: str,
) -> tuple[Path, EdifactFormatVersion]:
    """
    Run the setup shared by most commands: configure logging, check the Python version,
    ensure the output directory exists, and parse the requested format version.
    """
    setup_logging(verbose=verbose)
    check_python_version(console)
    output_path = ensure_output_path(console, output_path, assume_yes)
    efv = EdifactFormatVersion(format_version)
    return output_path, efv


def spinner_progress(console: Console) -> Progress:
    """Create an indeterminate spinner progress display."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )


def bar_progress(console: Console) -> Progress:
    """Create a progress bar display with item counts and elapsed time."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(pulse_style="cyan"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )
