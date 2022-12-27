"""
Main script of the AHB Extractor
"""
import re
from pathlib import Path
from typing import Optional

import click
import docx  # type:ignore[import]

from kohlrahbi.enums import FormatPrefix
from kohlrahbi.helper.read_functions import get_kohlrahbi
from kohlrahbi.logger import logger

_pruefi_pattern = re.compile(r"^[1-9]\d{4}$")


def get_valid_pruefis(list_of_pruefis: list[str]) -> list[str]:
    """
    This function returns only pruefis which match the pruefi_pattern.
    """
    valid_pruefis: list[str] = [pruefi for pruefi in list_of_pruefis if _pruefi_pattern.match(pruefi)]
    return valid_pruefis


def get_docx_files_which_may_contain_searched_pruefi(searched_pruefi: str, path_to_ahb_documents: Path) -> list[Path]:
    """
    This functions takes a pruefidentifikator and returns a list of docx files which can contain the searched pruefi.
    Unfortunately, it is not clear in which docx the pruefidentifikator you are looking for is located.
    A 11042 belongs to the UTILMD format. However, there are seven docx files that describe the UTILMD format.
    A further reduction of the number of files is not possible with the pruefidentifikator only.
    """

    pruefi_prefix: int = int(searched_pruefi[0:2])

    format: FormatPrefix = FormatPrefix(pruefi_prefix)

    docx_files_in_ahb_documents: list[Path] = [
        path
        for path in path_to_ahb_documents.iterdir()
        if path.is_file()
        if path.suffix == ".docx"
        if "AHB" in path.name
        if "LesefassungmitFehlerkorrekturen" in path.name
        if format.name in path.name
    ]

    return docx_files_in_ahb_documents


@click.command()
@click.option(
    "-p",
    "--pruefis",
    type=str,
    required=False,
    prompt="Pruefidentifikatoren you would like to get.",
    help="Five digit number like 11042.",
    multiple=True,
)
@click.option(
    "-i",
    "--input",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    prompt="Input directory",
    help="Define the path to the folder with the docx AHBs.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, path_type=Path),
    default="output",
    prompt="Output directory",
    help="Define the path where you want to save the generated files.",
)
def harvest(
    pruefis: Optional[list[str]],
    input: Path,
    output: Path,
):
    """
    A program to get a machine readable version of the AHBs docx files published by edi@energy.
    """

    # check if in- and output paths exist
    if not input.exists():
        click.secho("⚠️ The input directory does not exist.", fg="red")
        raise click.Abort()

    if not output.exists():
        click.secho("⚠️ The output directory does not exist.", fg="red")

        if click.confirm(f"Should I try to create the directory at '{output}'?", default=True):
            try:
                output.mkdir(exist_ok=True)
                click.secho("📂 The output directory is created.", fg="red")
            except FileNotFoundError as e:

                click.secho(
                    f"😱 There was an path error. I can only create a new directory in an already existing directory.",
                    fg="red",
                )
                click.secho(f"Your given path is '{output}'", fg="red")
                click.secho(str(e), fg="red")
                raise click.Abort()

        else:
            click.secho("👋 Alright I will end this program now. Have a nice day.", fg="green")
            raise click.Abort()

    output_directory_path: Path = Path.cwd() / Path("output")
    output_directory_path.mkdir(exist_ok=True)

    # check if one or more pruefidentifikatoren are given
    if pruefis is None:
        click.secho("☝️ No pruefis were given.", fg="yellow")
        raise click.Abort()

    valid_pruefis: list[str] = get_valid_pruefis(list_of_pruefis=pruefis)

    if valid_pruefis == []:
        click.secho("⚠️ There are no valid pruefidentifkatoren.", fg="red")
        raise click.Abort()

    if len(valid_pruefis) != len(pruefis):
        click.secho("☝️ Not all given pruefidentifikatoren are valid.", fg="yellow")
        click.secho(f"I will continue with the following valid pruefis: {valid_pruefis}.", fg="yellow")

    for pruefi in valid_pruefis:

        # find
        logger.info("start reading docx file(s)")
        # get_kohlrahbi(
        #     document=doc, root_output_directory_path=output_directory_path, ahb_file_name=ahb_file_path, pruefi="11016"
        # )
        print(pruefi)
        # continue


def main(file_paths: list[Path]) -> None:
    """
    Main function of the module kohlrahbi.
    It reads the docx files and calls the function to extract all Prüfindentifikatoren tables.
    """
    for ahb_file_path in file_paths:
        logger.info("Processing file '%s'", ahb_file_path)
        output_directory_path = Path.cwd() / Path("output")
        output_directory_path.mkdir(exist_ok=True)
        xlsx_out_path = output_directory_path / Path("xlsx")
        xlsx_out_path.mkdir(exist_ok=True)
        path_to_all_in_one_excel = xlsx_out_path / Path(str(ahb_file_path.parts[-1])[:-5] + ".xls")

        # Remove old "all in one Excel file" if it already exists
        if path_to_all_in_one_excel.exists():
            path_to_all_in_one_excel.unlink(missing_ok=False)

        try:
            doc = docx.Document(ahb_file_path)  # Creating word reader object.

        except IOError:
            logger.exception("There was an error opening the file '%s'", ahb_file_path, exc_info=True)

        logger.info("start reading docx file(s)")
        get_kohlrahbi(
            document=doc, root_output_directory_path=output_directory_path, ahb_file_name=ahb_file_path, pruefi="11016"
        )


if __name__ == "__main__":
    harvest()
