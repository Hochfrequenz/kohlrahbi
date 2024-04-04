"""
This module contains the functions to scrape the AHBs for Pruefidentifikatoren.
"""

import fnmatch
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

import click
import docx  # type: ignore
import tomlkit
from docx.document import Document  # type:ignore[import]
from docx.table import Table  # type:ignore[import]
from maus.edifact import EdifactFormatVersion

from kohlrahbi.ahbtable.ahbtable import AhbTable
from kohlrahbi.docxfilefinder import DocxFileFinder
from kohlrahbi.enums.ahbexportfileformat import AhbExportFileFormat
from kohlrahbi.logger import logger
from kohlrahbi.read_functions import (
    get_ahb_table,
    get_all_paragraphs_and_tables,
    table_header_starts_with_text_edifact_struktur,
)
from kohlrahbi.seed import Seed
from kohlrahbi.unfoldedahb import UnfoldedAhb

_pruefi_pattern = re.compile(r"^[1-9]\d{4}$")


def load_pruefi_docx_file_map_from_file(path_to_pruefi_docx_file_map_file: Path) -> dict[str, dict[str, str]]:
    """
    Loads the file which contains all known Prüfidentifikatoren.
    The file may be manually updated with the script `collect_pruefis.py`.
    """
    assert path_to_pruefi_docx_file_map_file.exists(), f"The file {path_to_pruefi_docx_file_map_file} does not exist."

    with open(path_to_pruefi_docx_file_map_file, "rb") as file:
        pruefi_docx_file_map: dict[str, str] = tomlkit.load(file)

    return pruefi_docx_file_map


def get_or_cache_document(ahb_file_path: Path, path_to_document_mapping: dict) -> Document:
    """
    Get the document from the cache or read it from the file system.
    """
    if ahb_file_path not in path_to_document_mapping:
        if not ahb_file_path.exists():
            logger.warning("The file '%s' does not exist", ahb_file_path)
            raise FileNotFoundError(f"The file '{ahb_file_path}' does not exist")
        try:
            doc = docx.Document(str(ahb_file_path))
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

        process_ahb_table(ahb_table, pruefi, output_path, file_type)


def get_ahb_documents_path(base_path: Path, version: str) -> Path:
    path = base_path / f"edi_energy_de/{version}"
    if not path.exists():
        raise FileNotFoundError(f"The specified path {path.absolute()} does not exist.")
    return path


def find_pruefidentifikatoren(path: Path) -> Dict[str, str]:
    pruefis = {}

    ahb_file_finder = DocxFileFinder.from_input_path(input_path=path)
    ahb_file_finder.filter_for_latest_ahb_docx_files()

    for docx_path in ahb_file_finder.paths_to_docx_files:
        pruefis.update(extract_pruefis_from_docx(docx_path))
    return dict(sorted(pruefis.items()))


def extract_pruefis_from_docx(docx_path: Path) -> Dict[str, str]:
    doc = docx.Document(str(docx_path))
    pruefis: dict[str, str] = {}
    for item in get_all_paragraphs_and_tables(doc):
        if (
            isinstance(item, Table)
            and table_header_starts_with_text_edifact_struktur(item)
            and table_header_contains_text_pruefidentifikator(item)
        ):
            pruefis.update({pruefi: docx_path.name for pruefi in extract_pruefis_from_table(item)})
    return pruefis


def save_pruefi_map_to_toml(pruefis: Dict[str, str], version: str) -> None:
    output_filename = f"{version}_pruefi_docx_filename_map.toml"
    output_file_path = Path(__file__).parents[1] / "cache" / output_filename
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    toml_data = {"meta_data": {"updated_on": date.today()}, "pruefidentifikatoren": pruefis}
    with open(output_file_path, "w", encoding="utf-8") as f:
        tomlkit.dump(toml_data, f)
        logger.info(f"🎉 Successfully updated {output_filename} and saved it at {output_file_path}.")


def log_no_pruefis_warning(version: str, path: Path) -> None:
    logger.warning(f"No Prüfidentifikatoren found in the AHB documents for format version {version} at {path}.")


def get_default_pruefi_map(path: Path) -> Dict[str, str]:
    return {"⚠️ No Prüfidentifikatoren found": f"No AHB documents found in {path}."}


def extract_pruefis_from_table(table: Table) -> list[str]:
    seed = Seed.from_table(docx_table=table)
    logger.info("Found a table with the following pruefis: %s", seed.pruefidentifikatoren)
    return seed.pruefidentifikatoren


def table_header_contains_text_pruefidentifikator(table: Table) -> bool:
    return table.row_cells(0)[-1].paragraphs[-1].text.startswith("Prüfidentifikator")


def create_pruefi_docx_filename_map(format_version: EdifactFormatVersion, edi_energy_mirror_path: Path):
    """ """
    all_pruefis: dict[str, str] = {}

    ahb_documents_path = get_ahb_documents_path(edi_energy_mirror_path, format_version)

    pruefis = find_pruefidentifikatoren(ahb_documents_path)

    if not pruefis:
        log_no_pruefis_warning(format_version.value, ahb_documents_path)
        pruefis = get_default_pruefi_map(ahb_documents_path)

    save_pruefi_map_to_toml(pruefis, format_version.value)


def get_pruefi_to_file_mapping(basic_input_path: Path, format_version: EdifactFormatVersion) -> dict[str, str]:
    default_path_to_cache_file = Path(__file__).parents[1] / "cache" / f"{format_version}_pruefi_docx_filename_map.toml"

    if default_path_to_cache_file.exists():
        pruefi_to_file_mapping_cache = load_pruefi_docx_file_map_from_file(default_path_to_cache_file)
        pruefi_to_file_mapping = pruefi_to_file_mapping_cache.get("pruefidentifikatoren")
        if isinstance(pruefi_to_file_mapping, type(None)):
            raise ReferenceError(f"Could not find pruefidentifikatoren in {default_path_to_cache_file}")
        return dict(pruefi_to_file_mapping)

    path_to_docx_files = basic_input_path / Path(f"edi_energy_de/{format_version}")
    pruefi_to_file_mapping = find_pruefidentifikatoren(path_to_docx_files)
    save_pruefi_map_to_toml(pruefi_to_file_mapping, format_version.value)
    return pruefi_to_file_mapping


def reduce_pruefi_to_file_mapping(pruefi_to_file_mapping: dict[str, str], pruefis: list[str]) -> dict[str, str | None]:
    """
    If the user provided pruefis, we filter the pruefi_to_file_mapping for these pruefis.
    """
    return {pruefi: filename for pruefi, filename in pruefi_to_file_mapping.items() if pruefi in pruefis}


def scrape_pruefis(
    pruefis: list[str],
    basic_input_path: Path,
    output_path: Path,
    file_type: AhbExportFileFormat,
    format_version: EdifactFormatVersion,
) -> None:
    """
    starts the scraping process for provided pruefi_to_file_mappings
    """

    pruefi_to_file_mapping = get_pruefi_to_file_mapping(
        basic_input_path=basic_input_path, format_version=format_version
    )
    if len(pruefis) > 0:
        validated_pruefis = validate_pruefis(pruefis)
        pruefi_to_file_mapping = reduce_pruefi_to_file_mapping(pruefi_to_file_mapping, validated_pruefis)

    path_to_document_mapping: dict[Path, Document] = {}

    for pruefi, filename in pruefi_to_file_mapping.items():
        try:
            logger.info("start looking for pruefi '%s'", pruefi)
            input_path = basic_input_path / Path("edi_energy_de") / Path(format_version.name)
            process_pruefi(pruefi, input_path, output_path, file_type, path_to_document_mapping)
        except FileNotFoundError:
            logger.exception("File not found for pruefi '%s'", pruefi)
        # sorry for the pokemon catch
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Error processing pruefi '%s': %s", pruefi, str(e))
