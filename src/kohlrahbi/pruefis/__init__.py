"""
This module contains the functions to scrape the AHBs for Pruefidentifikatoren.
"""

import fnmatch
import re
from pathlib import Path
from typing import Any, Optional

import click
import docx  # type: ignore
import tomlkit
from maus.edifact import EdifactFormat, EdifactFormatVersion

from kohlrahbi.ahb.ahbtable import AhbTable
from kohlrahbi.conditions import dump_conditions_json
from kohlrahbi.docxfilefinder import DocxFileFinder
from kohlrahbi.enums.ahbexportfileformat import AhbExportFileFormat
from kohlrahbi.logger import logger
from kohlrahbi.read_functions import get_ahb_table
from kohlrahbi.unfoldedahb import UnfoldedAhb

_pruefi_pattern = re.compile(r"^[1-9]\d{4}$")


def load_all_known_pruefis_from_file(
    path_to_all_known_pruefis: Path | None, format_version: EdifactFormatVersion
) -> dict[str, str | None]:
    """
    Loads the file which contains all known Prüfidentifikatoren.
    The file may be manually updated with the script `collect_pruefis.py`.
    """
    actual_path: Path
    if path_to_all_known_pruefis is None:
        actual_path = Path(__file__).parents[1] / "format_versions" / Path(f"{format_version}_all_known_pruefis.toml")
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


# pylint:disable=anomalous-backslash-in-string
def get_valid_pruefis(list_of_pruefis: list[str], all_known_pruefis: Optional[list[str]] = None) -> list[str]:
    """
    This function returns a list with only those pruefis which match the pruefi_pattern "^[1-9]\\d{4}$".
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


def scrape_pruefis(
    pruefi_to_file_mapping: dict[str, str | None],
    basic_input_path: Path,
    output_path: Path,
    file_type: AhbExportFileFormat,
    format_version: EdifactFormatVersion,
) -> None:
    """
    starts the scraping process for provided pruefi_to_file_mappings
    """
    pruefi_to_file_mapping = load_pruefis_if_empty(pruefi_to_file_mapping, format_version)

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
        except FileNotFoundError:
            logger.exception("File not found for pruefi '%s'", pruefi)
        # sorry for the pokemon catch
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Error processing pruefi '%s': %s", pruefi, str(e))

    if collected_conditions is not None:
        dump_conditions_json(output_path, collected_conditions)
