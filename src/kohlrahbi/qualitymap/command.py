"""
Command line interface for the qualitymap command.
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
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from kohlrahbi.logger import setup_logging

console = Console()

qualitymap_app = typer.Typer(invoke_without_command=True)


def check_python_version() -> None:
    """Check if the Python interpreter is greater or equal to 3.11"""
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        console.print("[red]Python >=3.11 is required to run this script.[/red]")
        raise typer.Exit(code=1)


@qualitymap_app.callback(invoke_without_command=True)
# pylint: disable-next=too-many-locals
def qualitymap(
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
    """Scrape quality maps from AHB documents."""
    setup_logging(verbose=verbose)
    check_python_version()

    from kohlrahbi.ahb.command import ensure_output_path

    output_path = ensure_output_path(output_path, assume_yes)
    efv = EdifactFormatVersion(format_version)
    input_path = edi_energy_mirror_path / "edi_energy_de" / efv.value

    from kohlrahbi.qualitymap import find_docx_files, process_docx_file

    ahb_file_paths = find_docx_files(input_path)
    total = len(ahb_file_paths)
    processed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(pulse_style="cyan"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scraping quality maps...", total=total)
        for file_path in ahb_file_paths:
            progress.update(task, description=f"Processing {file_path.name}...")
            quality_map_table = process_docx_file(file_path)
            if quality_map_table is not None:
                quality_map_table.save_to_csv(output_path / Path(f"{file_path.stem}_quality_map.csv"))
                quality_map_table.save_to_xlsx(output_path / Path(f"{file_path.stem}_quality_map.xlsx"))
                processed += 1
            progress.advance(task)

    console.print(
        Panel(
            f"[green]Processed:[/green] {processed}/{total} files\n" f"[blue]Output:[/blue]     {output_path}",
            title="Quality Map Scraping Complete",
            border_style="green",
        )
    )
