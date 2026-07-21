"""
kohlrahbi is a package to scrape AHBs (in docx format)
"""

import typer

from kohlrahbi.ahb.command import ahb_app
from kohlrahbi.changehistory.command import changehistory_app
from kohlrahbi.conditions.command import conditions_app
from kohlrahbi.qualitymap.command import qualitymap_app
from kohlrahbi.version import version


def version_callback(value: bool) -> None:
    """Print the version and exit."""
    if value:
        typer.echo(f"kohlrahbi version {version}")
        raise typer.Exit()


app = typer.Typer(help="Kohlrahbi CLI tool", no_args_is_help=True)
app.add_typer(ahb_app, name="ahb", help="Scrape AHB documents for pruefidentifikatoren.")
app.add_typer(changehistory_app, name="changehistory", help="Scrape change histories from EDIFACT documents.")
app.add_typer(conditions_app, name="conditions", help="Scrape AHB documents for conditions.")
app.add_typer(qualitymap_app, name="qualitymap", help="Scrape quality maps from AHB documents.")


@app.callback()
def main(
    _version: bool = typer.Option(
        False, "--version", "-V", callback=version_callback, is_eager=True, help="Show version and exit."
    ),
) -> None:
    """Kohlrahbi CLI tool"""


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
