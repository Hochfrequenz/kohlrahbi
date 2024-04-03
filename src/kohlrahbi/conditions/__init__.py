"""
This module contains the function to write the collected conditions to a json file.
"""

import json
from pathlib import Path
from typing import Optional

import docx
from maus.edifact import EdifactFormat, EdifactFormatVersion

from kohlrahbi.ahb.ahbcondtions import AhbConditions
from kohlrahbi.logger import logger
from kohlrahbi.pruefis import find_all_files_from_all_pruefis, load_pruefis_if_empty, validate_pruefis
from kohlrahbi.read_functions import get_all_conditions_from_doc


# pylint: disable=too-many-locals
def scrape_conditions(
    basic_input_path: Path,
    output_path: Path,
    format_version: EdifactFormatVersion,
) -> None:
    """
    starts the scraping process for conditions of all formats
    """
    pruefi_to_file_mapping: dict[str, str] = {}
    pruefi_to_file_mapping = load_pruefis_if_empty(pruefi_to_file_mapping, format_version)
    valid_pruefis = validate_pruefis(list(pruefi_to_file_mapping.keys()))
    valid_pruefi_to_file_mappings: dict[str, str | None] = {}
    for pruefi in valid_pruefis:
        valid_pruefi_to_file_mappings.update({pruefi: pruefi_to_file_mapping.get(pruefi, None)})

    collected_conditions: AhbConditions = AhbConditions()

    all_format_files = find_all_files_from_all_pruefis(valid_pruefi_to_file_mappings)
    for edifact_format, files in all_format_files.items():
        for file in files:
            # pylint: disable=too-many-function-args
            # type: ignore[call-arg, arg-type]
            doc = docx.Document(basic_input_path / Path(file))
            logger.info("Start scraping conditions for %s in %s", edifact_format, file)
            if not doc:
                logger.error("Could not open file %s as docx", Path(file))
            package_table, cond_table = get_all_conditions_from_doc(doc, edifact_format)
            if package_table:
                collected_conditions.include_condition_dict(package_table.provide_conditions(edifact_format))
            collected_conditions.include_condition_dict(cond_table.conditions_dict)
            test = 1

    collected_conditions.dump_as_json(output_path)
