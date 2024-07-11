"""
This module contains the functions to scrape the AHBs for Pruefidentifikatoren.
"""

import fnmatch
import gc
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

import click
import docx
import tomlkit
from docx.document import Document
from docx.table import Table
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
        pruefi_docx_file_map: dict[str, dict[str, str]] = tomlkit.load(file)

    return pruefi_docx_file_map


def process_ahb_table(
    ahb_table: AhbTable,
    pruefi: str,
    output_path: Path,
    file_type: tuple[AhbExportFileFormat, ...],
) -> None:
    """
    Process the ahb table.
    """
    unfolded_ahb = UnfoldedAhb.from_ahb_table(ahb_table=ahb_table, pruefi=pruefi)

    if AhbExportFileFormat.XLSX in file_type:
        unfolded_ahb.dump_xlsx(output_path)
    if AhbExportFileFormat.FLATAHB in file_type:
        unfolded_ahb.dump_flatahb_json(output_path)
    if AhbExportFileFormat.CSV in file_type:
        unfolded_ahb.dump_csv(output_path)
    del unfolded_ahb


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


def process_pruefi(
    pruefi: str,
    path_to_ahb_docx_file: Path,
    output_path: Path,
    file_type: tuple[AhbExportFileFormat, ...],
) -> None:
    """
    Process one pruefi.
    If the input path ends with .docx, we assume that the file containing the pruefi is given.
    Therefore we only access that file.
    """

    # TODO try to cache document objects cause it is slow to read them from disk # pylint: disable=fixme
    doc = docx.Document(str(path_to_ahb_docx_file))

    if not doc:
        return

    ahb_table = get_ahb_table(document=doc, pruefi=pruefi)
    if not ahb_table:
        return

    process_ahb_table(ahb_table, pruefi, output_path, file_type)
    del ahb_table.table
    del ahb_table
    del doc
    gc.collect()


def get_ahb_documents_path(base_path: Path, version: str) -> Path:
    """Returns the path to the AHB documents for the specified format version."""
    path = base_path / f"edi_energy_de/{version}"
    if not path.exists():
        raise FileNotFoundError(f"The specified path {path.absolute()} does not exist.")
    return path


def find_pruefidentifikatoren(path: Path) -> Dict[str, str]:
    """finds pruefis in given dir"""
    pruefis = {}

    ahb_file_finder = DocxFileFinder.from_input_path(input_path=path)
    ahb_file_finder.filter_for_latest_ahb_docx_files()

    for docx_path in ahb_file_finder.paths_to_docx_files:
        pruefis.update(extract_pruefis_from_docx(docx_path))
    return dict(sorted(pruefis.items()))


def extract_pruefis_from_docx(docx_path: Path) -> Dict[str, str]:
    """Extracts the Prüfidentifikatoren from the given docx file."""
    doc = docx.Document(str(docx_path))
    pruefis: dict[str, str] = {}
    for item in get_all_paragraphs_and_tables(doc):
        if (
            isinstance(item, Table)
            and table_header_starts_with_text_edifact_struktur(item)
            and table_header_contains_text_pruefidentifikator(item)
        ):
            # pylint:disable=not-an-iterable
            pruefis.update({pruefi: docx_path.name for pruefi in extract_pruefis_from_table(item)})
    return pruefis


def save_pruefi_map_to_toml(pruefis: Dict[str, str], version: str) -> None:
    """Saves the pruefis to file mapping to a toml file."""
    output_filename = f"{version}_pruefi_docx_filename_map.toml"
    output_file_path = Path(__file__).parents[1] / "cache" / output_filename
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    toml_data = {"meta_data": {"updated_on": date.today()}, "pruefidentifikatoren": pruefis}
    with open(output_file_path, "w", encoding="utf-8") as f:
        tomlkit.dump(toml_data, f)
        logger.info("🎉 Successfully updated %s and saved it at %s.", output_filename, output_file_path)


def log_no_pruefis_warning(version: str, path: Path) -> None:
    """Logs a warning if no Prüfidentifikatoren were found."""
    logger.warning("No Prüfidentifikatoren found in the AHB documents for format version %s at %s.", version, path)


def get_default_pruefi_map(path: Path) -> Dict[str, str]:
    """Returns a default pruefi map if no pruefis were found."""
    return {"⚠️ No Prüfidentifikatoren found": f"No AHB documents found in {path}."}


def extract_pruefis_from_table(table: Table) -> list[str]:
    """Extracts the Prüfidentifikatoren from given table."""
    seed = Seed.from_table(docx_table=table)
    logger.info("Found a table with the following pruefis: %s", seed.pruefidentifikatoren)
    return seed.pruefidentifikatoren


def table_header_contains_text_pruefidentifikator(table: Table) -> bool:
    """Checks if the table header contains the text 'Prüfidentifikator'."""
    pattern = r"Prüfidentifikator(?:\t){0,10}\t\d+"
    # "matches "Prüfidentifikator" followed by at least 1 tab separated numbers, max 11 pruefis is chosen arbitrarily
    return bool(re.search(pattern, table.row_cells(0)[-1].text))


def get_pruefi_to_file_mapping(basic_input_path: Path, format_version: EdifactFormatVersion) -> dict[str, str]:
    """Returns the pruefi to file mapping. If the cache file does not exist, it creates it."""
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


def reduce_pruefi_to_file_mapping(pruefi_to_file_mapping: dict[str, str], pruefis: list[str]) -> dict[str, str]:
    """
    If the user provided pruefis, we filter the pruefi_to_file_mapping for these pruefis.
    """
    return {pruefi: filename for pruefi, filename in pruefi_to_file_mapping.items() if pruefi in pruefis}


def scrape_pruefis(
    pruefis: list[str],
    basic_input_path: Path,
    output_path: Path,
    file_type: tuple[AhbExportFileFormat, ...],
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

    for pruefi, filename in pruefi_to_file_mapping.items():
        try:
            logger.info("start looking for pruefi '%s'", pruefi)
            if not filename:
                logger.warning("No filename for pruefi '%s' provided", pruefi)
                continue
            path_to_ahb_docx_file = (
                basic_input_path / Path("edi_energy_de") / Path(format_version.name) / Path(filename)
            )
            process_pruefi(pruefi, path_to_ahb_docx_file, output_path, file_type)
        except FileNotFoundError:
            logger.exception("File not found for pruefi '%s'", pruefi)
        # sorry for the pokemon catch
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Error processing pruefi '%s': %s", pruefi, str(e))
