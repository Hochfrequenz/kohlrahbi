"""
Main script of the Kohlrahbi
"""
import re
import sys
from pathlib import Path
from typing import Any

import click
import docx  # type:ignore[import]
import tomlkit
from maus.edifact import EdifactFormat, get_format_of_pruefidentifikator

from kohlrahbi.ahb.ahbtable import AhbTable
from kohlrahbi.logger import logger
from kohlrahbi.read_functions import get_ahb_table
from kohlrahbi.unfoldedahb.unfoldedahbtable import UnfoldedAhb

_pruefi_pattern = re.compile(r"^[1-9]\d{4}$")


def get_valid_pruefis(list_of_pruefis: list[str]) -> list[str]:
    """
    This function returns only pruefis which match the pruefi_pattern.
    """
    valid_pruefis: list[str] = [pruefi for pruefi in list_of_pruefis if _pruefi_pattern.match(pruefi)]
    return valid_pruefis


def get_all_ahb_docx_files(path_to_ahb_documents: Path) -> list[Path]:
    """
    Get all paths to the latest AHB docx files.
    The latest files contain `LesefassungmitFehlerkorrekturen` in their file names.
    """
    return [
        path
        for path in path_to_ahb_documents.iterdir()
        if path.is_file()
        if path.suffix == ".docx"
        if "AHB" in path.name
        if "LesefassungmitFehlerkorrekturen" in path.name
    ]


def filter_docx_files_for_edifact_format(list_of_ahb_docx_paths: list[Path], edifact_format: EdifactFormat):
    """
    Filter the list of AHB docx paths for the given EDIFACT format
    """

    return [path for path in list_of_ahb_docx_paths if str(edifact_format) in path.name]


def get_docx_files_which_may_contain_searched_pruefi(searched_pruefi: str, path_to_ahb_documents: Path) -> list[Path]:
    """
    This functions takes a pruefidentifikator and returns a list of docx files which can contain the searched pruefi.
    Unfortunately, it is not clear in which docx the pruefidentifikator you are looking for is located.
    A 11042 belongs to the UTILMD format. However, there are seven docx files that describe the UTILMD format.
    A further reduction of the number of files is not possible with the pruefidentifikator only.
    """

    edifact_format = get_format_of_pruefidentifikator(searched_pruefi)
    if edifact_format is None:
        logger.exception("❌ There is no known format known for the prüfi '%s'.", searched_pruefi)
        return []

    docx_files_in_ahb_documents = get_all_ahb_docx_files(path_to_ahb_documents=path_to_ahb_documents)

    filtered_docx_files_in_ahb_documents = filter_docx_files_for_edifact_format(
        list_of_ahb_docx_paths=docx_files_in_ahb_documents, edifact_format=edifact_format
    )

    return filtered_docx_files_in_ahb_documents


def check_python_version():
    """
    Check if the Python interpreter is greater or equal to 3.11
    """
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        raise click.Abort(
            f"""Python >=3.11 is required to run this script but you use Python
{sys.version_info.major}.{sys.version_info.minor}"""
        )


def check_input_path(path: Path) -> None:
    """
    Checks if the given path exists.
    Iff it does NOT exist a error message gets printed to inform the user.
    """
    if not path.exists():
        click.secho("⚠️ The input directory does not exist.", fg="red")
        raise click.Abort()


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

    # would be happy for name suggestions for "loaded_toml"
    # it contains only two sections: meta_data and content
    # meta_data holds the updated_on date
    # content a list of all known pruefis
    with open(path_to_all_known_pruefis, "rb") as file:
        loaded_toml: dict[str, Any] = tomlkit.load(file)

    meta_data_section = loaded_toml.get("meta_data")
    content_section = loaded_toml.get("content")

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
def harvest(
    pruefis: list[str],
    input_path: Path,
    output_path: Path,
    file_type: list[str],
):
    """
    A program to get a machine readable version of the AHBs docx files published by edi@energy.
    """
    check_python_version()

    check_input_path(path=input_path)

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
        ahb_file_paths: list[Path] = get_docx_files_which_may_contain_searched_pruefi(
            searched_pruefi=pruefi, path_to_ahb_documents=input_path
        )

        for ahb_file_path in ahb_file_paths:
            try:
                doc = docx.Document(ahb_file_path)  # Creating word reader object.

            except IOError as ioe:
                logger.exception("There was an error opening the file '%s'", ahb_file_path, exc_info=True)
                raise click.Abort() from ioe

            logger.info("start reading docx file(s)")

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
                    unfolded_ahb.to_xlsx(path_to_output_directory=output_directory_path)

                if "flatahb" in file_type:
                    unfolded_ahb.to_flatahb_json(output_directory_path=output_directory_path)

                if "csv" in file_type:
                    unfolded_ahb.to_csv(path_to_output_directory=output_directory_path)

                break


if __name__ == "__main__":
    # the parameter arguments gets provided over the CLI
    harvest()  # pylint:disable=no-value-for-parameter
