"""
This module contains the function to write the collected conditions to a json file.
"""

import json
from pathlib import Path
from typing import Optional

import docx
from maus.edifact import EdifactFormat

from kohlrahbi import get_package_table
from kohlrahbi.logger import logger
from kohlrahbi.pruefis import (
    find_all_files_from_all_pruefis,
    get_or_cache_document,
    load_pruefis_if_empty,
    process_pruefi,
    validate_pruefis,
)


def process_package_conditions(
    input_path: Path,
    path_to_document_mapping: dict,
    collected_conditions: Optional[dict[EdifactFormat, dict[str, str]]],
    edifact_format: EdifactFormat,
):
    """
    Processes one docx document.
    If the input path ends with .docx, we assume that the file containing the pruefi is given.
    Therefore, we only access that file.
    """
    if not input_path.suffix == ".docx":
        raise ValueError(("The input path %s for scraping package conditions must be a docx file.", input_path))
    doc = get_or_cache_document(input_path, path_to_document_mapping)
    if not doc:
        return

    package_table = get_package_table(document=doc)
    if package_table:
        package_table.collect_conditions(collected_conditions, edifact_format)  # type: ignore[arg-type]


# pylint: disable=too-many-locals
def scrape_conditions(
    pruefi_to_file_mapping: dict[str, str | None],
    basic_input_path: Path,
    output_path: Path,
) -> None:
    """
    starts the scraping process for conditions of all formats
    """
    are_pruefis_provided = bool(pruefi_to_file_mapping)
    pruefi_to_file_mapping = load_pruefis_if_empty(pruefi_to_file_mapping)
    valid_pruefis = validate_pruefis(list(pruefi_to_file_mapping.keys()))
    valid_pruefi_to_file_mappings: dict[str, str | None] = {}
    for pruefi in valid_pruefis:
        valid_pruefi_to_file_mappings.update({pruefi: pruefi_to_file_mapping.get(pruefi, None)})
    path_to_document_mapping: dict[Path, docx.Document] = {}
    collected_conditions: Optional[dict[EdifactFormat, dict[str, str]]] = {}
    for pruefi, filename in valid_pruefi_to_file_mappings.items():
        try:
            logger.info("start looking for pruefi '%s'", pruefi)
            input_path = basic_input_path  # To prevent multiple adding of filenames
            # that would happen if filenames are added but never removed
            if filename is not None:
                input_path = basic_input_path / Path(filename)
            process_pruefi(
                pruefi, input_path, output_path, "conditions", path_to_document_mapping, collected_conditions
            )
        # sorry for the pokemon catch
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Error processing pruefi '%s': %s", pruefi, str(e))
    all_format_files = find_all_files_from_all_pruefis(valid_pruefi_to_file_mappings)
    if not are_pruefis_provided:
        for edifact_format, files in all_format_files.items():
            for file in files:
                # pylint: disable=too-many-function-args
                # type: ignore[call-arg, arg-type]
                process_package_conditions(
                    basic_input_path / Path(file), path_to_document_mapping, collected_conditions, edifact_format
                )
    dump_conditions_json(output_path, collected_conditions)  # type: ignore[arg-type]


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
