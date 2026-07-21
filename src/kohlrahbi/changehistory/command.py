"""
Command line interface for the changehistory commands.
"""

# pylint: disable=import-outside-toplevel
# Heavy submodules are imported lazily inside the command functions so that `--help` stays fast.

import asyncio
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

changehistory_app = typer.Typer(no_args_is_help=True)


def check_python_version() -> None:
    """Check if the Python interpreter is greater or equal to 3.11"""
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        console.print("[red]Python >=3.11 is required to run this script.[/red]")
        raise typer.Exit(code=1)


@changehistory_app.command("docx")
# pylint: disable-next=too-many-locals
def docx(
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
    """Scrape change histories from .docx files in the edi_energy_mirror repository."""
    setup_logging(verbose=verbose)
    check_python_version()

    from kohlrahbi.ahb.command import ensure_output_path

    output_path = ensure_output_path(output_path, assume_yes)
    efv = EdifactFormatVersion(format_version)
    input_path = edi_energy_mirror_path / "edi_energy_de"

    from kohlrahbi.changehistory import extract_sheet_name, process_docx_file, save_change_histories_to_excel
    from kohlrahbi.docxfilefinder import DocxFileFinder

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Finding change history files...", total=None)
        path_to_files = DocxFileFinder(path_to_edi_energy_mirror=input_path).get_file_paths_for_change_history(
            format_version=efv
        )

    total = len(path_to_files)
    processed = 0
    skipped: list[str] = []
    change_history_collection: dict[str, object] = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(pulse_style="cyan"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting change histories...", total=total)
        for file_path in path_to_files:
            progress.update(task, description=f"Processing {file_path.name}...")
            df = process_docx_file(file_path)
            if df is not None:
                change_history_collection[extract_sheet_name(file_path.name)] = df
                processed += 1
            else:
                skipped.append(file_path.name)
            progress.advance(task)

    save_change_histories_to_excel(change_history_collection, output_path)  # type: ignore[arg-type]

    from kohlrahbi.docxfiledescriptor import summarize_version_tiers_from_paths

    tier_summary = summarize_version_tiers_from_paths(path_to_files)

    skipped_info = ""
    if skipped:
        skipped_list = "\n".join(f"  - {name}" for name in skipped)
        skipped_info = f"\n[yellow]Skipped (no change history table found):[/yellow]\n{skipped_list}"

    console.print(
        Panel(
            f"[green]Processed:[/green]  {processed}/{total} files\n"
            f"[cyan]Source docs:[/cyan]  {tier_summary}{skipped_info}\n"
            f"[blue]Output:[/blue]       {output_path}",
            title="Change History Extraction Complete",
            border_style="green",
        )
    )


@changehistory_app.command("bnetza")
def bnetza(
    url: Annotated[
        str,
        typer.Option(
            "--url",
            help="The BNetzA URL to scrape for PDF documents.",
        ),
    ] = ...,  # type: ignore[assignment]
    output_path: Annotated[
        Path,
        typer.Option(
            "-o",
            "--output-path",
            help="Define the path where you want to save the downloaded PDFs and generated Excel file.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("output"),
    verbose: Annotated[
        bool,
        typer.Option(
            "-v",
            "--verbose",
            help="Enable verbose logging output.",
        ),
    ] = False,
) -> None:
    """Download PDFs from a BNetzA URL and extract change histories."""
    setup_logging(verbose=verbose)
    check_python_version()

    from kohlrahbi.changehistory.bnetza import download_pdfs

    output_path.mkdir(parents=True, exist_ok=True)
    pdf_dir = output_path / "pdfs"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Downloading and processing PDFs from BNetzA...", total=None)
        asyncio.run(download_pdfs(url=url, target_dir=pdf_dir))

    console.print(
        Panel(
            f"[blue]Output:[/blue] {output_path}",
            title="BNetzA Change History Extraction Complete",
            border_style="green",
        )
    )
