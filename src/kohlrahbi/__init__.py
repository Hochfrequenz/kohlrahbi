"""
kohlrahbi is a package to scrape AHBs (in docx format)
"""
import fnmatch
import gc
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional

import click
import docx  # type:ignore[import]
import pandas as pd
import tomlkit
from maus.edifact import EdifactFormat

from kohlrahbi.ahb.ahbtable import AhbTable
from kohlrahbi.changehistory.changehistorytable import ChangeHistoryTable
from kohlrahbi.docxfilefinder import DocxFileFinder
from kohlrahbi.logger import logger
from kohlrahbi.read_functions import get_ahb_table, get_change_history_table
from kohlrahbi.unfoldedahb.unfoldedahbtable import UnfoldedAhb

_pruefi_pattern = re.compile(r"^[1-9]\d{4}$")


# pylint:disable=anomalous-backslash-in-string
def get_valid_pruefis(list_of_pruefis: list[str], all_known_pruefis: Optional[list[str]] = None) -> list[str]:
    """
    This function returns a new list with only those pruefis which match the pruefi_pattern r"^[1-9]\d{4}$".
    It also supports unix wildcards like '*' and '?' iff a list of known pruefis is given.
    E.g. '11*' for all pruefis starting with '11' or '*01' for all pruefis ending with '01'.
    """
    result: set[str] = set()

    for pruefi in list_of_pruefis:
        if ("*" in pruefi or "?" in pruefi) and all_known_pruefis:
            filtered_pruefis = fnmatch.filter(all_known_pruefis, pruefi)
            result = result.union(filtered_pruefis)
        elif _pruefi_pattern.match(pruefi):
            result.add(pruefi)

    return sorted(list(result))


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
                click.secho(f"📂 The output directory is created at {path.absolute()}.", fg="yellow")
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
    The file may be manually updated with the script `collect_pruefis.py`.
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


def create_sheet_name(filename: str) -> str:
    """
    Creates a sheet name from the filename.

    We need to shorten the sheet name because Excel only allows 31 characters for sheet names.
    This function replaces some words with acronyms and removes some words.
    """
    sheet_name = filename.split("-informatorischeLesefassung")[0]

    if "Entscheidungsbaum-Diagramm" in sheet_name:
        sheet_name = sheet_name.replace("Entscheidungsbaum", "EBDs")
    if "Artikelnummern" in sheet_name:
        sheet_name = sheet_name.replace("Artikelnummern", "Artikelnr")
    if "Codeliste" in sheet_name:
        sheet_name = sheet_name.replace("Codeliste", "CL")
    if len(sheet_name) > 31:
        # Excel only allows 31 characters for sheet names
        # but REQOTEQUOTESORDERSORDRSPORDCHGAHB is 33 characters long
        sheet_name = sheet_name.replace("HG", "")
    return sheet_name


def scrape_change_histories(input_path: Path, output_path: Path) -> None:
    """
    starts the scraping process of the change histories
    """
    logger.info("start looking for change histories")
    docx_file_finder = DocxFileFinder.from_input_path(input_path=input_path)
    ahb_file_paths: list[Path] = docx_file_finder.get_all_docx_files_which_contain_change_histories()

    change_history_collection: dict[str, pd.DataFrame] = {}

    for ahb_file_path in ahb_file_paths:
        # extract the sheet name from the file name
        # COMDISAHB-informatorischeLesefassung1.0e_99991231_20240401.docx -> COMDISAHB
        sheet_name = create_sheet_name(ahb_file_path.name)

        doc = docx.Document(ahb_file_path)  # Creating word reader object.
        logger.info("🤓 Start reading docx file '%s'", str(ahb_file_path))
        change_history_table: ChangeHistoryTable = get_change_history_table(document=doc)

        if change_history_table is None:
            continue
        change_history_table.sanitize_table()

        change_history_collection[sheet_name] = change_history_table.table

    # add timestamp to file name
    # there are two timestamps: one with datetime and another one with just date information.
    # It is handy during debugging to save different versions of the output files with the datetime information.
    # But in production we only want to save one file per day.
    # current_timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    current_timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    path_to_change_history_excel_file = output_path / f"{current_timestamp}_change_histories.xlsx"

    logger.info("💾 Saving change histories xlsx file %s", path_to_change_history_excel_file)

    # Define column widths (example: 20, 15, 30, etc.)
    column_widths = [6, 6, 46, 52, 52, 38, 15]  # Replace with your desired widths

    # Create a Pandas Excel writer using XlsxWriter as the engine
    # https://github.com/PyCQA/pylint/issues/3060 pylint: disable=abstract-class-instantiated
    with pd.ExcelWriter(path_to_change_history_excel_file, engine="xlsxwriter") as writer:
        for sheet_name, df in change_history_collection.items():
            df.to_excel(writer, sheet_name=sheet_name)

            # Access the XlsxWriter workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # Create a text wrap format
            wrap_format = workbook.add_format({"text_wrap": True})

            # Get the dimensions of the DataFrame
            (max_row, max_col) = df.shape

            assert max_col + 1 == len(column_widths)  # +1 cause of index

            # Apply text wrap format to each cell
            for col_num, width in enumerate(column_widths):
                worksheet.set_column(col_num, col_num, width, wrap_format)


def scrape_pruefis(
    pruefis: list[str], input_path: Path, output_path: Path, file_type: Literal["flatahb", "csv", "xlsx", "conditions"]
) -> None:
    """
    starts the scraping process for provided pruefis
    """

    if not any(pruefis):
        click.secho("☝️ No pruefis were given. I will parse all known pruefis.", fg="yellow")
        pruefis = load_all_known_pruefis_from_file()
    if not any(file_type):
        message = "ℹ You did not provide any value for the parameter --file-type. No files will be created."
        click.secho(message, fg="yellow")
        logger.warning(message)

    valid_pruefis: list[str] = get_valid_pruefis(list_of_pruefis=pruefis)
    if not any(valid_pruefis):
        click.secho("⚠️ There are no valid pruefidentifkatoren.", fg="red")
        raise click.Abort()

    if len(valid_pruefis) != len(pruefis):
        click.secho("☝️ Not all given pruefidentifikatoren are valid.", fg="yellow")
        click.secho(f"I will continue with the following valid pruefis: {valid_pruefis}.", fg="yellow")
    path_to_document_mapping: dict[Path, docx.Document] = {}

    if "conditions" in file_type:
        # mapping of EdifactFormat to ConditionKeyConditionTextMapping for all given prufis
        collected_conditions: dict[EdifactFormat, dict[str, str]] = {}

    for pruefi in valid_pruefis:
        try:
            logger.info("start looking for pruefi '%s'", pruefi)
            ahb_file_finder = DocxFileFinder.from_input_path(input_path=input_path)
            ahb_file_paths: list[Path] = ahb_file_finder.get_docx_files_which_may_contain_searched_pruefi(
                searched_pruefi=pruefi
            )

            if not any(ahb_file_paths):
                logger.warning("No docx file was found for pruefi '%s'", pruefi)
                continue

            for ahb_file_path in ahb_file_paths:
                if not (doc := path_to_document_mapping.get(ahb_file_path, None)):
                    try:
                        doc = docx.Document(ahb_file_path)  # Creating word reader object.
                        path_to_document_mapping[ahb_file_path] = doc
                        logger.debug("Saved %s document in cache", ahb_file_path)  # to not re-read it every time
                    except IOError as ioe:
                        logger.exception("There was an error opening the file '%s'", ahb_file_path, exc_info=True)
                        raise click.Abort() from ioe

                logger.info("🤓 Start reading docx file '%s'", str(ahb_file_path))

                ahb_table: AhbTable | None = get_ahb_table(
                    document=doc,
                    pruefi=pruefi,
                )

                if ahb_table is None:
                    continue

                if isinstance(ahb_table, AhbTable):
                    unfolded_ahb = UnfoldedAhb.from_ahb_table(ahb_table=ahb_table, pruefi=pruefi)

                    if "xlsx" in file_type:
                        logger.info("💾 Saving xlsx file %s", pruefi)
                        unfolded_ahb.dump_xlsx(path_to_output_directory=output_path)

                    if "flatahb" in file_type:
                        logger.info("💾 Saving flatahb file %s", pruefi)
                        unfolded_ahb.dump_flatahb_json(output_directory_path=output_path)

                    if "csv" in file_type:
                        logger.info("💾 Saving csv file %s", pruefi)
                        unfolded_ahb.dump_csv(path_to_output_directory=output_path)

                    if "conditions" in file_type:
                        logger.info("🧺 Collecting conditions file %s", pruefi)
                        unfolded_ahb.collect_condition(already_known_conditions=collected_conditions)

                    break
        except Exception as general_error:  # pylint:disable=broad-except
            logger.exception(
                "There was an uncaught error while processing the pruefi '%s': %s",
                pruefi,
                str(general_error),
                exc_info=True,
            )
            continue
        del ahb_table
        del ahb_file_finder
        if "unfolded_ahb" in locals():
            del unfolded_ahb
        gc.collect()

    if "conditions" in file_type:
        # store conditions in conditions.json files
        dump_conditions_json(output_directory_path=output_path, already_known_conditions=collected_conditions)


@click.command()
@click.option(
    "-f",
    "--flavour",
    type=click.Choice(["pruefi", "changehistory"], case_sensitive=False),
    default="pruefi",
    help='Choose between "pruefi" and "changehistory".',
)
@click.option(
    "-p",
    "--pruefis",
    default=[],
    required=False,
    help="Five digit number like 11042 or use wildcards like 110* or *042 or 11?42.",
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
    type=click.Choice(["flatahb", "csv", "xlsx", "conditions"], case_sensitive=False),
    multiple=True,
)
@click.option(
    "--assume-yes",
    "-y",
    is_flag=True,
    help="Confirm all prompts automatically.",
)
# pylint: disable=too-many-arguments
def main(
    flavour: str, pruefis: list[str], input_path: Path, output_path: Path, file_type: list[str], assume_yes: bool
) -> None:
    """
    A program to get a machine readable version of the AHBs docx files published by edi@energy.
    """
    check_python_version()

    if not assume_yes:
        check_output_path(path=output_path)
    else:
        if output_path.exists():
            click.secho(f"The output directory '{output_path}' exists already.", fg="yellow")
        else:
            output_path.mkdir(parents=True)
            click.secho(f"I created a new directory at {output_path}", fg="yellow")

    match flavour:
        case "pruefi":
            scrape_pruefis(
                pruefis=pruefis,
                input_path=input_path,
                output_path=output_path,
                file_type=file_type,
            )
        case "changehistory":
            scrape_change_histories(input_path=input_path, output_path=output_path)


def dump_conditions_json(output_directory_path: Path, already_known_conditions: dict) -> None:
    """
    Writes all collected conditions to a json file.
    The file will be stored in the directory:
        'output_directory_path/<edifact_format>/conditions.json'
    """
    for edifact_format in already_known_conditions:
        condition_json_output_directory_path = output_directory_path / str(edifact_format)
        condition_json_output_directory_path.mkdir(parents=True, exist_ok=True)
        file_path = condition_json_output_directory_path / "conditions.json"
        # resort  ConditionKeyConditionTextMappings for output
        sorted_condition_dict = {
            k: already_known_conditions[edifact_format][k]
            for k in sorted(already_known_conditions[edifact_format], key=int)
        }
        array = [
            {"condition_key": i, "condition_text": sorted_condition_dict[i], "edifact_format": edifact_format}
            for i in sorted_condition_dict
        ]
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(array, file, ensure_ascii=False, indent=2)

        logger.info(
            "The conditions.json file for %s is saved at %s",
            edifact_format,
            file_path,
        )


if __name__ == "__main__":
    # the parameter arguments gets provided over the CLI
    main()  # pylint:disable=no-value-for-parameter
