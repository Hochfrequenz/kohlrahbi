"""
Command line interface for the changehistory commands.
"""

# pylint: disable=import-outside-toplevel
# Heavy submodules are imported lazily inside the command functions so that `--help` stays fast.

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from kohlrahbi.cli_utils import bar_progress, check_python_version, prepare_command, spinner_progress
from kohlrahbi.logger import setup_logging

console = Console()

changehistory_app = typer.Typer(no_args_is_help=True)


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
    output_path, efv = prepare_command(
        console=console, verbose=verbose, output_path=output_path, assume_yes=assume_yes, format_version=format_version
    )
    input_path = edi_energy_mirror_path / "edi_energy_de"

    from kohlrahbi.changehistory import extract_sheet_name, process_docx_file, save_change_histories_to_excel
    from kohlrahbi.docxfilefinder import DocxFileFinder

    with spinner_progress(console) as progress:
        progress.add_task("Finding change history files...", total=None)
        path_to_files = DocxFileFinder(path_to_edi_energy_mirror=input_path).get_file_paths_for_change_history(
            format_version=efv
        )

    total = len(path_to_files)
    processed = 0
    skipped: list[str] = []
    change_history_collection: dict[str, object] = {}

    with bar_progress(console) as progress:
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
    """Download documents from a BNetzA URL and extract change histories."""
    setup_logging(verbose=verbose)
    check_python_version(console)

    from kohlrahbi.changehistory.bnetza import DownloadResult, download_documents

    output_path.mkdir(parents=True, exist_ok=True)
    pdf_dir = output_path / "pdfs"

    with bar_progress(console) as progress:
        download_task = progress.add_task("Discovering documents...", total=None)
        extract_task = progress.add_task("Extracting change histories...", total=None, visible=False)

        def on_links_found(total: int) -> None:
            progress.update(download_task, description="Downloading documents...", total=total)

        def on_downloaded(result: DownloadResult) -> None:
            progress.update(download_task, description=f"Downloaded {result.stem}")
            progress.advance(download_task)

        def on_extract_start(total: int) -> None:
            progress.update(extract_task, total=total, visible=True)

        def on_extracted(name: str) -> None:
            progress.update(extract_task, description=f"Extracting {name}")
            progress.advance(extract_task)

        summary = asyncio.run(
            download_documents(
                url=url,
                target_dir=pdf_dir,
                on_links_found=on_links_found,
                on_downloaded=on_downloaded,
                on_extract_start=on_extract_start,
                on_extracted=on_extracted,
            )
        )

    kinds = ", ".join(f"{count}×{kind}" for kind, count in sorted(summary.kinds.items())) or "none"
    cached = f"  [dim]+{summary.skipped} cached[/dim]" if summary.skipped else ""
    lines = [
        f"[green]Links found:[/green]   {summary.links_found}",
        f"[green]Downloaded:[/green]    {summary.downloaded} ({kinds}){cached}",
        f"[green]Sheets written:[/green] {len(summary.sheets)}",
    ]
    if summary.no_change_history:
        no_ch = "\n".join(f"  - {name}" for name in summary.no_change_history)
        lines.append(f"[yellow]No change history:[/yellow]\n{no_ch}")
    if summary.failed_processing:
        failed_proc = "\n".join(f"  - {name}" for name in summary.failed_processing)
        lines.append(f"[red]Failed to process:[/red]\n{failed_proc}")
    if summary.failed_downloads:
        failed_dl = "\n".join(f"  - {name}" for name in summary.failed_downloads)
        lines.append(f"[red]Failed downloads:[/red]\n{failed_dl}")
    output_line = summary.output_file if summary.output_file else f"{output_path} (no Excel written)"
    lines.append(f"[blue]Output:[/blue]        {output_line}")

    console.print(
        Panel(
            "\n".join(lines),
            title="BNetzA Change History Extraction Complete",
            border_style="green",
        )
    )
