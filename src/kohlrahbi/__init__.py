"""
kohlrahbi is a package to scrape AHBs (in docx format)
"""

import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import Any, Literal, Optional

import click
import docx  # type:ignore[import]
import tomlkit
from maus.edifact import EdifactFormat, EdifactFormatVersion

from kohlrahbi.ahb.ahbtable import AhbTable
from kohlrahbi.changehistory.functions import scrape_change_histories
from kohlrahbi.docxfilefinder import DocxFileFinder
from kohlrahbi.logger import logger
from kohlrahbi.read_functions import get_ahb_table
from kohlrahbi.unfoldedahb.unfoldedahbtable import UnfoldedAhb

_pruefi_pattern = re.compile(r"^[1-9]\d{4}$")


# pylint:disable=anomalous-backslash-in-string
def get_valid_pruefis(list_of_pruefis: list[str], all_known_pruefis: Optional[list[str]] = None) -> list[str]:
    """
    This function returns a list with only those pruefis which match the pruefi_pattern r"^[1-9]\d{4}$".
    It also supports unix wildcards like '*' and '?' if a list of known pruefis is given.
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


def validate_path(ctx, param, value):
    """
    Ensure the path exists or offer to create it.
    """
    path = Path(value)
    if not path.exists():
        if ctx.params.get("assume_yes") or click.confirm(
            f"The path {value} does not exist. Would you like to create it?"
        ):
            path.mkdir(parents=True)
            click.secho(f"Created directory {path}.", fg="green")
        else:
            click.secho("👋 Alright I will end this program now. Have a nice day.", fg="green")
            raise click.Abort()
    return path


def load_all_known_pruefis_from_file(
    path_to_all_known_pruefis: Path | None, format_version: EdifactFormatVersion
) -> dict[str, str | None]:
    """
    Loads the file which contains all known Prüfidentifikatoren.
    The file may be manually updated with the script `collect_pruefis.py`.
    """
    actual_path: Path
    if path_to_all_known_pruefis is None:
        actual_path = Path(__file__).parent / "format_versions" / Path(f"{format_version}_all_known_pruefis.toml")
    else:
        actual_path = path_to_all_known_pruefis
    with open(actual_path, "rb") as file:
        state_of_kohlrahbi: dict[str, Any] = tomlkit.load(file)

    meta_data_section = state_of_kohlrahbi.get("meta_data")
    pruefi_to_file_mapping: dict[str, str | None] | None = state_of_kohlrahbi.get("pruefidentifikatoren", None)

    if meta_data_section is None:
        click.secho(f"There is no 'meta_data' section in the provided toml file: {path_to_all_known_pruefis}", fg="red")
        raise click.Abort()
    if pruefi_to_file_mapping is None:
        click.secho(
            f"There is no 'pruefidentifikatoren' section in the toml file: {path_to_all_known_pruefis}", fg="red"
        )
        raise click.Abort()

    return pruefi_to_file_mapping


def load_pruefis_if_empty(
    pruefi_to_file_mapping: dict[str, str | None], format_version: EdifactFormatVersion
) -> dict[str, str | None]:
    """
    If the user did not provide any pruefis we load all known pruefis
    and the paths to the file containing them from the toml file.
    """
    if not pruefi_to_file_mapping:
        click.secho("☝️ No pruefis were given. I will parse all known pruefis.", fg="yellow")
        return load_all_known_pruefis_from_file(path_to_all_known_pruefis=None, format_version=format_version)
    return pruefi_to_file_mapping


# TODO remove this function when we have a better solution
# use the required parameter in the click.option decorator
def validate_file_type(file_type: str):
    """
    Validate the file type parameter.
    """
    if not file_type:
        message = "ℹ You did not provide any value for the parameter --file-type. No files will be created."
        click.secho(message, fg="yellow")
        logger.warning(message)


def validate_pruefis(pruefis: list[str]) -> list[str]:
    """
    Validate the pruefi_to_file_mapping parameter.
    """
    valid_pruefis = get_valid_pruefis(pruefis)
    if not valid_pruefis:
        click.secho("⚠️ There are no valid pruefidentifkatoren.", fg="red")
        raise click.Abort()
    return valid_pruefis


# pylint: disable=too-many-arguments
def process_pruefi(
    pruefi: str,
    input_path: Path,
    output_path: Path,
    file_type: str,
    path_to_document_mapping: dict,
    collected_conditions: Optional[dict[EdifactFormat, dict[str, str]]],
):
    """
    Process one pruefi.
    If the input path ends with .docx, we assume that the file containing the pruefi is given.
    Therefore we only access that file.
    """
    if not input_path.suffix == ".docx":
        ahb_file_finder = DocxFileFinder.from_input_path(input_path=input_path)
        ahb_file_paths = ahb_file_finder.get_docx_files_which_may_contain_searched_pruefi(pruefi)
    else:
        ahb_file_paths = [input_path]

    if not ahb_file_paths:
        logger.warning("No docx file was found for pruefi '%s'", pruefi)
        return

    for ahb_file_path in ahb_file_paths:
        doc = get_or_cache_document(ahb_file_path, path_to_document_mapping)
        if not doc:
            return

        ahb_table = get_ahb_table(document=doc, pruefi=pruefi)
        if not ahb_table:
            return

        process_ahb_table(ahb_table, pruefi, output_path, file_type, collected_conditions)


def get_or_cache_document(ahb_file_path: Path, path_to_document_mapping: dict) -> docx.Document:
    """
    Get the document from the cache or read it from the file system.
    """
    if ahb_file_path not in path_to_document_mapping:
        if not ahb_file_path.exists():
            logger.warning("The file '%s' does not exist", ahb_file_path)
            raise FileNotFoundError(f"The file '{ahb_file_path}' does not exist")
        try:
            doc = docx.Document(ahb_file_path)
            path_to_document_mapping[ahb_file_path] = doc
            logger.debug("Saved %s document in cache", ahb_file_path)
        except IOError as ioe:
            logger.exception("There was an error opening the file '%s'", ahb_file_path, exc_info=True)
            raise click.Abort() from ioe
    return path_to_document_mapping[ahb_file_path]


def process_ahb_table(
    ahb_table: AhbTable,
    pruefi: str,
    output_path: Path,
    file_type: str,
    collected_conditions: Optional[dict[EdifactFormat, dict[str, str]]],
):
    """
    Process the ahb table.
    """
    unfolded_ahb = UnfoldedAhb.from_ahb_table(ahb_table=ahb_table, pruefi=pruefi)

    if "xlsx" in file_type:
        unfolded_ahb.dump_xlsx(output_path)
    if "flatahb" in file_type:
        unfolded_ahb.dump_flatahb_json(output_path)
    if "csv" in file_type:
        unfolded_ahb.dump_csv(output_path)
    if "conditions" in file_type:
        unfolded_ahb.collect_condition(collected_conditions)


def scrape_pruefis(
    pruefi_to_file_mapping: dict[str, str | None],
    basic_input_path: Path,
    output_path: Path,
    file_type: Literal["flatahb", "csv", "xlsx", "conditions"],
    format_version: EdifactFormatVersion,
) -> None:
    """
    starts the scraping process for provided pruefi_to_file_mappings
    """
    pruefi_to_file_mapping = load_pruefis_if_empty(pruefi_to_file_mapping, format_version)
    validate_file_type(file_type)

    valid_pruefis = validate_pruefis(list(pruefi_to_file_mapping.keys()))
    valid_pruefi_to_file_mappings: dict[str, str | None] = {}
    for pruefi in valid_pruefis:
        valid_pruefi_to_file_mappings.update({pruefi: pruefi_to_file_mapping.get(pruefi, None)})
    path_to_document_mapping: dict[Path, docx.Document] = {}
    collected_conditions: Optional[dict[EdifactFormat, dict[str, str]]] = {} if "conditions" in file_type else None

    for pruefi, filename in valid_pruefi_to_file_mappings.items():
        try:
            logger.info("start looking for pruefi '%s'", pruefi)
            input_path = basic_input_path  # To prevent multiple adding of filenames
            # that would happen if filenames are added but never removed
            if filename is not None:
                input_path = basic_input_path / Path(filename)
            process_pruefi(pruefi, input_path, output_path, file_type, path_to_document_mapping, collected_conditions)
        except FileNotFoundError as fnfe:
            # logger.exception("File not found for pruefi '%s': %s", pruefi, str(fnfe))
            logger.exception("File not found for pruefi '%s'", pruefi)
        # sorry for the pokemon catch
        # except Exception as e:  # pylint: disable=broad-except
        #     logger.exception("Error processing pruefi '%s': %s", pruefi, str(e))

    if collected_conditions is not None:
        dump_conditions_json(output_path, collected_conditions)


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
    "--input-path",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    prompt="Input directory",
    help="Define the path to the folder with the docx AHBs.",
)
@click.option(
    "-o",
    "--output-path",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True, path_type=Path),
    callback=validate_path,
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
    "--format-version",
    multiple=False,
    type=click.Choice([e.value for e in EdifactFormatVersion], case_sensitive=False),
    help="Format version(s) of the AHB documents, e.g. FV2310",
)
@click.option(
    "--assume-yes",
    "-y",
    is_flag=True,
    default=False,
    help="Confirm all prompts automatically.",
)
# pylint: disable=too-many-arguments
def main(
    flavour: str,
    pruefis: list[str],
    input_path: Path,
    output_path: Path,
    file_type: Literal["flatahb", "csv", "xlsx", "conditions"],
    format_version: EdifactFormatVersion | str,
    assume_yes: bool,
) -> None:
    """
    A program to get a machine readable version of the AHBs docx files published by edi@energy.
    """
    check_python_version()
    if isinstance(format_version, str):
        format_version = EdifactFormatVersion(format_version)

    pruefi_to_file_mapping: dict[str, str | None] = {
        key: None for key in pruefis
    }  # A mapping of a pruefi (key) to the name (+ path) of the file containing the prufi
    match flavour:
        case "pruefi":
            scrape_pruefis(
                pruefi_to_file_mapping=pruefi_to_file_mapping,
                basic_input_path=input_path,
                output_path=output_path,
                file_type=file_type,
                format_version=format_version,
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
