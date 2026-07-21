"""
Command line interface for the qualitymap command.
"""

# pylint: disable=import-outside-toplevel
# Heavy submodules are imported lazily inside the command functions so that `--help` stays fast.

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from kohlrahbi.cli_utils import bar_progress, prepare_command

console = Console()

qualitymap_app = typer.Typer(invoke_without_command=True)


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
    output_path, efv = prepare_command(
        console=console, verbose=verbose, output_path=output_path, assume_yes=assume_yes, format_version=format_version
    )
    input_path = edi_energy_mirror_path / "edi_energy_de" / efv.value

    from kohlrahbi.qualitymap import find_docx_files, process_docx_file

    ahb_file_paths = find_docx_files(input_path)
    total = len(ahb_file_paths)
    processed = 0

    with bar_progress(console) as progress:
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
