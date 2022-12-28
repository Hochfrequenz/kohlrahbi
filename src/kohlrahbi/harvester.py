"""
Main script of the AHB Extractor
"""
import re
from pathlib import Path
from typing import Any

import click
import docx  # type:ignore[import]
import toml
from maus.edifact import pruefidentifikator_to_format

from kohlrahbi.dump import dump_kohlrahbi_to_csv, dump_kohlrahbi_to_excel, dump_kohlrahbi_to_flatahb
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

    edifact_format = pruefidentifikator_to_format(searched_pruefi)
    if edifact_format is None:
        logger.exception("❌ There is no known format known for the prüfi '%s'.", searched_pruefi)
        return []

    docx_files_in_ahb_documents: list[Path] = [
        path
        for path in path_to_ahb_documents.iterdir()
        if path.is_file()
        if path.suffix == ".docx"
        if "AHB" in path.name
        if "LesefassungmitFehlerkorrekturen" in path.name
        if str(edifact_format) in path.name
    ]

    return docx_files_in_ahb_documents


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
@click.option(
    "--file-type",
    type=click.Choice(["flatahb", "csv", "xlsx"], case_sensitive=False),
    multiple=True,
)
def harvest(
    pruefis: list[str],
    input: Path,
    output: Path,
    file_type: list[str],
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
                click.secho("📂 The output directory is created.", fg="yellow")
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
    if len(pruefis) == 0:
        click.secho("☝️ No pruefis were given. I will parse all known pruefis.", fg="yellow")

        # would be happy for name suggestions for "loaded_toml"
        # it contains only two sections meta_data and content
        # meta_data holds the updated_on date and content a list of all known pruefis
        path_to_all_known_pruefis: Path = Path(__file__).parent / Path("all_known_pruefis.toml")
        loaded_toml: dict[str, Any] = toml.load(path_to_all_known_pruefis)

        meta_data_section = loaded_toml.get("meta_data")
        content_section = loaded_toml.get("content")

        if meta_data_section is None:
            click.secho(
                f"There is no 'meta_data' section in the provided toml file: {path_to_all_known_pruefis}", fg="red"
            )
            click.Abort()
        if content_section is None:
            click.secho(f"There is no 'content' section in the toml file: {path_to_all_known_pruefis}", fg="red")
            click.Abort()

        pruefis = content_section.get("pruefidentifikatoren")

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
            searched_pruefi=pruefi, path_to_ahb_documents=input
        )

        for ahb_file_path in ahb_file_paths:

            try:
                doc = docx.Document(ahb_file_path)  # Creating word reader object.

            except IOError:
                logger.exception("There was an error opening the file '%s'", ahb_file_path, exc_info=True)
                click.Abort()

            logger.info("start reading docx file(s)")

            kohlrahbi = get_kohlrahbi(
                document=doc,
                root_output_directory_path=output_directory_path,
                ahb_file_name=ahb_file_path,
                pruefi=pruefi,
            )

            if kohlrahbi is None:
                continue
            else:
                # save kohlrahbi
                logger.info("💾 Saving kohlrahbi %s \n", pruefi)
                if "xlsx" in file_type:
                    dump_kohlrahbi_to_excel(
                        kohlrahbi=kohlrahbi,
                        pruefi=pruefi,
                        output_directory_path=output_directory_path,
                    )
                if "flatahb" in file_type:
                    dump_kohlrahbi_to_flatahb(
                        kohlrahbi=kohlrahbi,
                        pruefi=pruefi,
                        output_directory_path=output_directory_path,
                    )
                if "csv" in file_type:
                    dump_kohlrahbi_to_csv(
                        kohlrahbi=kohlrahbi,
                        pruefi=pruefi,
                        output_directory_path=output_directory_path,
                    )


if __name__ == "__main__":
    harvest()
