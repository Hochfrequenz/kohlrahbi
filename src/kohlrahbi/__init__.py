"""
kohlrahbi is a package to scrape AHBs (in docx format)
"""

import click

from kohlrahbi.ahb.command import ahb
from kohlrahbi.changehistory.command import changehistory
from kohlrahbi.conditions.command import conditions


@click.group()
def cli():
    """Kohlrahbi CLI tool"""


# Add commands to the CLI group
cli.add_command(ahb)
cli.add_command(changehistory)
cli.add_command(conditions)

if __name__ == "__main__":
    # the parameter arguments gets provided over the CLI
    cli()  # pylint:disable=no-value-for-parameter
