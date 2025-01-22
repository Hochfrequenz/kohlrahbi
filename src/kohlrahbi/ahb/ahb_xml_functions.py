"""
Contains functions to scrape content from xml files.
"""

from pathlib import Path

import tomlkit
from efoli import EdifactFormatVersion
from fundamend import AhbReader, Anwendungshandbuch

from kohlrahbi.ahb import save_pruefi_map_to_toml
from kohlrahbi.enums.ahbexportfileformat import AhbExportFileFormat
from kohlrahbi.logger import logger
from kohlrahbi.unfoldedahb import UnfoldedAhb
from kohlrahbi.unfoldedahb.unfoldedahbtable import are_equal_except_for_guids


def process_pruefi(
    pruefi: str, input_path: Path, output_path: Path, file_type: tuple[AhbExportFileFormat, ...]
) -> None:
    """
    Opens xml file and processes pruefi.
    """
    reader = AhbReader(input_path)
    ahb = reader.read()
    assert isinstance(ahb, Anwendungshandbuch)
    assert pruefi in {awf.pruefidentifikator for awf in ahb.anwendungsfaelle}
    unfolded_ahb: UnfoldedAhb = None
    for awf in ahb.anwendungsfaelle:
        if awf.pruefidentifikator == pruefi:
            unfolded_ahb = UnfoldedAhb.from_xml_ahb(ahb_table=awf)
            break

    try:
        json_file_path = unfolded_ahb.get_flatahb_json_file_path(output_path)
        excel_file_path = unfolded_ahb.get_xlsx_file_path(output_path)
        csv_file_path = unfolded_ahb.get_csv_file_path(output_path)
    except ValueError:
        logger.warning("Error while determining file paths for pruefi '%s'. Skipping saving files.", pruefi)
        return
    pruefi_did_change_since_last_scraping: bool = True  # we assume it yes, if we can't compare or unless we know better
    if AhbExportFileFormat.FLATAHB in file_type and json_file_path.exists():
        # the flat ahb is the only file format from which we can READ to compare our current with previous results
        pruefi_did_change_since_last_scraping = not are_equal_except_for_guids(unfolded_ahb, json_file_path)
        logger.info("Pruefi '%s' did change since last scraping: %s", pruefi, pruefi_did_change_since_last_scraping)
    # ⚠ here we assume that the csv/json/xlsx files are in sync, if they exist.
    # this means: if the json file didn't change and a csv file exists, we expect the csv file to also be unchanged
    excel_needs_to_be_dumped = AhbExportFileFormat.XLSX in file_type and (
        (not excel_file_path.exists()) or pruefi_did_change_since_last_scraping
    )
    json_needs_to_be_dumped = AhbExportFileFormat.FLATAHB in file_type and (
        (not json_file_path.exists()) or pruefi_did_change_since_last_scraping
    )
    csv_needs_to_be_dumped = AhbExportFileFormat.CSV in file_type and (
        (not csv_file_path.exists()) or pruefi_did_change_since_last_scraping
    )
    if excel_needs_to_be_dumped:
        unfolded_ahb.dump_xlsx(output_path)
    if json_needs_to_be_dumped:
        unfolded_ahb.dump_flatahb_json(output_path)
    if csv_needs_to_be_dumped:
        unfolded_ahb.dump_csv(output_path)
    del unfolded_ahb
    print(1)


def scrape_xml_pruefis(
    pruefis: list[str],
    input_path: Path,
    output_path: Path,
    file_type: tuple[AhbExportFileFormat, ...],
    format_version: EdifactFormatVersion,
) -> None:
    """
    Proof of concept.
    """
    input_path = input_path / Path("UTILMD_AHB-Strom_2_1_2024_10_01_2024_09_20.xml")
    for pruefi in pruefis:
        process_pruefi(pruefi, input_path, output_path, file_type)
