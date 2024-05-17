"""
This module contains the function to write the collected conditions to a json file.
"""

from pathlib import Path

import docx
from maus.edifact import EdifactFormat, EdifactFormatVersion, get_format_of_pruefidentifikator

from kohlrahbi.ahb import get_pruefi_to_file_mapping
from kohlrahbi.ahbtable.ahbcondtions import AhbConditions
from kohlrahbi.ahbtable.ahbpackagetable import AhbPackageTable
from kohlrahbi.logger import logger
from kohlrahbi.read_functions import get_all_conditions_from_doc


def find_all_files_from_all_pruefis(pruefi_to_file_mapping: dict[str, str]) -> dict[EdifactFormat, list[str]]:
    """takes list of all pruefis with according files and returns a dict edifactformat-> list(filepaths)"""
    format_to_files_mapping: dict[EdifactFormat, list[str]] = {}
    for pruefi, filename in pruefi_to_file_mapping.items():
        if not filename:
            raise ValueError(f"No file provided for pruefi {pruefi}")
        edifact_format = get_format_of_pruefidentifikator(pruefi)
        if format_to_files_mapping.get(edifact_format) is None:
            format_to_files_mapping[edifact_format] = [filename]
        elif filename not in format_to_files_mapping[edifact_format]:
            format_to_files_mapping[edifact_format].append(filename)
    return format_to_files_mapping


def scrape_conditions(
    basic_input_path: Path,
    output_path: Path,
    format_version: EdifactFormatVersion,
) -> None:
    """
    starts the scraping process for conditions of all formats
    """
    path_to_file = basic_input_path / Path("edi_energy_de") / Path(format_version.value)
    pruefi_to_file_mapping = get_pruefi_to_file_mapping(basic_input_path, format_version)

    collected_conditions: AhbConditions = AhbConditions()
    collected_packages: AhbPackageTable = AhbPackageTable()
    all_format_files = find_all_files_from_all_pruefis(pruefi_to_file_mapping)
    for edifact_format, files in all_format_files.items():
        for file in files:
            # pylint: disable=too-many-function-args
            path: Path = basic_input_path / path_to_file / Path(file)
            doc = docx.Document(str(path.absolute()))
            logger.info("Start scraping conditions for %s in %s", edifact_format, file)
            if not doc:
                logger.error("Could not open file %s as docx", Path(file))
            packages, cond_table = get_all_conditions_from_doc(doc, edifact_format)
            if packages and packages.table is not None:
                collected_conditions.include_condition_dict(packages.provide_conditions(edifact_format))
                collected_packages.include_package_dict(packages.package_dict)
            collected_conditions.include_condition_dict(cond_table.conditions_dict)
    collected_conditions.dump_as_json(output_path)
    collected_packages.dump_as_json(output_path)
