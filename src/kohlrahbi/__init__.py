"""
kohlrahbi is a package to scrape AHBs (in docx format)
"""


import re
import sys
from pathlib import Path
from typing import Any

import click
import docx  # type:ignore[import]
import tomlkit

from kohlrahbi.ahb.ahbtable import AhbTable
from kohlrahbi.ahbfilefinder import AhbFileFinder
from kohlrahbi.logger import logger
from kohlrahbi.read_functions import get_ahb_table
from kohlrahbi.unfoldedahb.unfoldedahbtable import UnfoldedAhb

_pruefi_pattern = re.compile(r"^[1-9]\d{4}$")


def get_valid_pruefis(list_of_pruefis: list[str]) -> list[str]:
    """
    This function returns a new list with only those pruefis which match the pruefi_pattern.
    """
    valid_pruefis: list[str] = [pruefi for pruefi in list_of_pruefis if _pruefi_pattern.match(pruefi)]
    return valid_pruefis


def check_python_version():
    """
    Check if the Python interpreter is greater or equal to 3.11
    """
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        raise click.Abort(
            f"""Python >=3.11 is required to run this script but you use Python
{sys.version_info.major}.{sys.version_info.minor}"""
        )


def check_output_path(path: Path) -> None:
    """
    Checks if the given path exists and if not it asks the user if they want to create the given directory.
    """
    if not path.exists():
        click.secho("⚠️ The output directory does not exist.", fg="red")

        if click.confirm(f"Should I try to create the directory at '{path}'?", default=True):
            try:
                path.mkdir(exist_ok=True)
                click.secho("📂 The output directory is created.", fg="yellow")
            except FileNotFoundError as fnfe:
                click.secho(
                    "😱 There was an path error. I can only create a new directory in an already existing directory.",
                    fg="red",
                )
                click.secho(f"Your given path is '{path}'", fg="red")
                click.secho(str(fnfe), fg="red")
                raise click.Abort()

        else:
            click.secho("👋 Alright I will end this program now. Have a nice day.", fg="green")
            raise click.Abort()


def load_all_known_pruefis_from_file(
    path_to_all_known_pruefis: Path = Path(__file__).parent / Path("all_known_pruefis.toml"),
) -> list[str]:
    """
    Loads the file which contains all known Prüfidentifikatoren.
    """

    with open(path_to_all_known_pruefis, "rb") as file:
        state_of_kohlrahbi: dict[str, Any] = tomlkit.load(file)

    meta_data_section = state_of_kohlrahbi.get("meta_data")
    content_section = state_of_kohlrahbi.get("content")

    if meta_data_section is None:
        click.secho(f"There is no 'meta_data' section in the provided toml file: {path_to_all_known_pruefis}", fg="red")
        raise click.Abort()
    if content_section is None:
        click.secho(f"There is no 'content' section in the toml file: {path_to_all_known_pruefis}", fg="red")
        raise click.Abort()

    pruefis: list[str] = content_section.get("pruefidentifikatoren")
    return pruefis


@click.command()
@click.option(
    "-p",
    "--pruefis",
    default=[],
    required=False,
    help="Five digit number like 11042.",
    multiple=True,
)
@click.option(
    "-i",
    "--input_path",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    prompt="Input directory",
    help="Define the path to the folder with the docx AHBs.",
)
@click.option(
    "-o",
    "--output_path",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, path_type=Path),
    default="output",
    prompt="Output directory",
    help="Define the path where you want to save the generated files.",
)
@click.option(
    "--file-type",
    type=click.Choice(["flatahb", "csv", "xlsx"], case_sensitive=False),
    multiple=True,
)
def main(
    pruefis: list[str],
    input_path: Path,
    output_path: Path,
    file_type: list[str],
):
    """
    A program to get a machine readable version of the AHBs docx files published by edi@energy.
    """
    check_python_version()

    check_output_path(path=output_path)

    output_directory_path: Path = Path.cwd() / Path("output")
    output_directory_path.mkdir(exist_ok=True)

    if len(pruefis) == 0:
        click.secho("☝️ No pruefis were given. I will parse all known pruefis.", fg="yellow")
        pruefis = load_all_known_pruefis_from_file()

    valid_pruefis: list[str] = get_valid_pruefis(list_of_pruefis=pruefis)

    if valid_pruefis == []:
        click.secho("⚠️ There are no valid pruefidentifkatoren.", fg="red")
        raise click.Abort()

    if len(valid_pruefis) != len(pruefis):
        click.secho("☝️ Not all given pruefidentifikatoren are valid.", fg="yellow")
        click.secho(f"I will continue with the following valid pruefis: {valid_pruefis}.", fg="yellow")

    for pruefi in valid_pruefis:
        logger.info("start looking for pruefi '%s'", pruefi)

        ahb_file_finder = AhbFileFinder.from_input_path(input_path=input_path)

        ahb_file_paths: list[Path] = ahb_file_finder.get_docx_files_which_may_contain_searched_pruefi(
            searched_pruefi=pruefi
        )

        for ahb_file_path in ahb_file_paths:
            try:
                doc = docx.Document(ahb_file_path)  # Creating word reader object.

            except IOError as ioe:
                logger.exception("There was an error opening the file '%s'", ahb_file_path, exc_info=True)
                raise click.Abort() from ioe

            logger.info("start reading docx file(s) '%s'", str(ahb_file_path))

            ahb_table: AhbTable | None = get_ahb_table(
                document=doc,
                pruefi=pruefi,
            )

            if ahb_table is None:
                continue

            if isinstance(ahb_table, AhbTable):
                unfolded_ahb = UnfoldedAhb.from_ahb_table(ahb_table=ahb_table, pruefi=pruefi)

                logger.info("💾 Saving files %s \n", pruefi)
                if "xlsx" in file_type:
                    unfolded_ahb.dump_xlsx(path_to_output_directory=output_directory_path)

                if "flatahb" in file_type:
                    unfolded_ahb.dump_flatahb_json(output_directory_path=output_directory_path)

                if "csv" in file_type:
                    unfolded_ahb.dump_csv(path_to_output_directory=output_directory_path)

                break


if __name__ == "__main__":
    # the parameter arguments gets provided over the CLI
    main()  # pylint:disable=no-value-for-parameter
