"""
Command line interface for the pruefis module.
"""

import sys
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from efoli import EdifactFormatVersion
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from kohlrahbi.enums.ahbexportfileformat import AhbExportFileFormat
from kohlrahbi.logger import setup_logging

console = Console()

ahb_app = typer.Typer(invoke_without_command=True)


def check_python_version() -> None:
    """
    Check if the Python interpreter is greater or equal to 3.11
    """
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        console.print("[red]Python >=3.11 is required to run this script.[/red]")
        raise typer.Exit(code=1)


def ensure_output_path(output_path: Path, assume_yes: bool) -> Path:
    """Ensure the output path exists or offer to create it."""
    if not output_path.exists():
        if assume_yes or typer.confirm(f"The path {output_path} does not exist. Would you like to create it?"):
            output_path.mkdir(parents=True)
            console.print(f"[green]Created directory {output_path}.[/green]")
        else:
            console.print("[green]Alright, exiting. Have a nice day.[/green]")
            raise typer.Exit()
    return output_path


@ahb_app.callback(invoke_without_command=True)
def ahb(
    pruefis: Annotated[
        list[str],
        typer.Option(
            "-p",
            "--pruefis",
            help="Five digit number like 11042 or use wildcards like 110* or *042 or 11?42.",
        ),
    ] = [],  # noqa: B006
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
    file_type: Annotated[
        list[AhbExportFileFormat],
        typer.Option(
            "--file-type",
            help="File type(s) for the scraped AHB documents.",
            case_sensitive=False,
        ),
    ] = ...,  # type: ignore[assignment]
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
    clear_output_path: Annotated[
        bool,
        typer.Option(
            "--clear-output-path",
            help="Clear old removed files from existing output path.",
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
    Scrape AHB documents for pruefidentifikatoren.
    """
    setup_logging(verbose=verbose)
    check_python_version()
    output_path = ensure_output_path(output_path, assume_yes)

    efv = EdifactFormatVersion(format_version)

    from kohlrahbi.ahb import get_pruefi_to_file_mapping, process_pruefi, remove_vanished_pruefis, validate_pruefis

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Loading pruefi mapping...", total=None)
        pruefi_to_file_mapping = get_pruefi_to_file_mapping(
            basic_input_path=edi_energy_mirror_path, format_version=efv, pruefis=pruefis
        )

    if pruefis:
        try:
            validated_pruefis = validate_pruefis(pruefis)
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(code=1) from e
        from kohlrahbi.ahb import reduce_pruefi_to_file_mapping

        pruefi_to_file_mapping = reduce_pruefi_to_file_mapping(pruefi_to_file_mapping, validated_pruefis)
        not_found_pruefis = [p for p in validated_pruefis if p not in pruefi_to_file_mapping]
        if not_found_pruefis:
            console.print(
                f"[yellow]Warning:[/yellow] No AHB document found for pruefidentifikator(en) "
                f"{', '.join(not_found_pruefis)} in format version {format_version}."
            )

    if clear_output_path:
        remove_vanished_pruefis(pruefi_to_file_mapping, output_path)

    total = len(pruefi_to_file_mapping)
    processed = 0
    skipped_no_filename: list[str] = []
    skipped_not_found: list[str] = []
    skipped_errors: list[tuple[str, str]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(pulse_style="cyan"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scraping AHB documents...", total=total)
        for pruefi, filename in pruefi_to_file_mapping.items():
            progress.update(task, description=f"Processing pruefi {pruefi}...")
            try:
                if not filename:
                    skipped_no_filename.append(pruefi)
                    continue
                path_to_ahb_docx_file = edi_energy_mirror_path / Path("edi_energy_de") / Path(efv.name) / Path(filename)
                process_pruefi(pruefi, path_to_ahb_docx_file, output_path, tuple(file_type))
                processed += 1
            except FileNotFoundError:
                skipped_not_found.append(pruefi)
            except Exception as e:  # pylint: disable=broad-except
                skipped_errors.append((pruefi, str(e)))
            progress.advance(task)

    from kohlrahbi.docxfiledescriptor import summarize_version_tiers

    used_filenames = [fn for fn in pruefi_to_file_mapping.values() if fn]
    tier_summary = summarize_version_tiers(list(set(used_filenames)))

    details = ""
    if skipped_no_filename:
        details += f"\n[yellow]No filename mapped:[/yellow] {', '.join(skipped_no_filename)}"
    if skipped_not_found:
        details += f"\n[yellow]File not found:[/yellow]     {', '.join(skipped_not_found)}"
    if skipped_errors:
        error_lines = "\n".join(f"  - {p}: {msg}" for p, msg in skipped_errors)
        details += f"\n[red]Errors:[/red]\n{error_lines}"

    console.print(
        Panel(
            f"[green]Processed:[/green]  {processed}/{total} pruefidentifikatoren\n"
            f"[cyan]Source docs:[/cyan]  {tier_summary}{details}\n"
            f"[blue]Output:[/blue]       {output_path}",
            title="AHB Scraping Complete",
            border_style="green" if not skipped_errors else "yellow",
        )
    )
