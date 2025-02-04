"""
This module provides functions for scraping change histories from .docx files and saving them to an Excel file.

The main functions in this module are:
- `scrape_change_histories`: Starts the scraping process of the change histories.
- `find_docx_files`: Finds all .docx files containing change histories.
- `process_docx_file`: Reads and processes change history from a .docx file.
- `save_change_histories_to_excel`: Saves the collected change histories to an Excel file.
- `create_sheet_name`: Creates a sheet name from the filename.
"""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import docx
import pandas as pd
from docx.document import Document
from docx.table import Table
from efoli import EdifactFormatVersion

from kohlrahbi.changehistory.changehistorytable import ChangeHistoryTable
from kohlrahbi.docxfilefinder import DocxFileFinder
from kohlrahbi.logger import logger
from kohlrahbi.read_functions import get_all_paragraphs_and_tables


def is_change_history_table(table: Table) -> bool:
    """
    Checks if the given table is change history table.
    """
    # in the document 'Entscheidungsbaum-DiagrammeundCodelisten-informatorischeLesefassung3.5_99991231_20240401.docx'
    # I got the error "IndexError: list index out of range", I am not sure which table caused the error
    try:
        return table.cell(row_idx=0, col_idx=0).text.strip() == "Änd-ID"
    except IndexError:
        return False


def get_change_history_table(document: Document) -> Optional[ChangeHistoryTable]:
    """
    Reads a docx file and extracts the change history.
    Returns None if no such table was found.
    """

    # Iterate through the whole word document
    logger.info("🔁 Start iterating through paragraphs and tables")
    for item in get_all_paragraphs_and_tables(parent=document):
        if isinstance(item, Table) and is_change_history_table(table=item):
            change_history_table = ChangeHistoryTable.from_docx_change_history_table(docx_table=item)
            return change_history_table

    return None


def extract_sheet_name(filename: str) -> str:
    """
    Extract and format a valid Excel sheet name from a filename.
    The sheet name will be no longer than 31 characters (Excel's limit).

    Args:
        filename (str): The full filename like 'AHB_COMDIS_1.0f_20250606_99991231_20250606_ooox_8871.docx'
                       or 'Entscheidungsbaum-DiagrammeundCodelisten-informatorischeLesefassung3.5.docx'
                       or 'EBD_4.0b_20250606_20250131_20241215_xoxx_11449.docx'

    Returns:
        str: The extracted sheet name, shortened to max 31 chars

    Examples:
        >>> extract_sheet_name("AHB_COMDIS_1.0f_20250606_99991231_20250606_ooox_8871.docx")
        'AHB_COMDIS_1.0f'
        >>> extract_sheet_name("MIG_UTILMD_2.1e_20250606_99991231_20250131_xoxx_11449.docx")
        'MIG_UTILMD_2.1e'
        >>> extract_sheet_name("EBD_4.0b_20250606_20250131_20241215_xoxx_11449.docx")
        'EBD_4.0b'
    """
    # First try to extract format and version for standard AHB/MIG/EBD files
    pattern = r"^((?:AHB|MIG|EBD)_[A-Z]*_?[0-9]+\.[0-9]+[a-zA-Z]*)"
    match = re.match(pattern, filename)
    if match:
        sheet_name = match.group(1)
    else:
        # Handle special cases like Entscheidungsbaum files
        sheet_name = filename.split("-informatorischeLesefassung")[0]
        # Apply replacements for common long terms
        replacements = {
            "Entscheidungsbaum": "EBDs",
            "Diagramme": "",
            "und": "_",
            "Artikelnummern": "Artikelnr",
            "Codeliste": "CL",
            "HG": "",  # Special case for REQOTEQUOTESORDERSORDRSPORDCHGAHB
            "allgemeinefestlegungeninformatorischelesefassung": "Allgemeine Festlegungen",
            "apiguidelineinformatorischelesefassung": "API Guideline",
        }
        for old, new in replacements.items():
            sheet_name = sheet_name.replace(old, new)

        # Extract version if present (assuming it's at the end like '3.5')
        version_pattern = r".*?([0-9]+\.[0-9]+[a-zA-Z]*)$"
        version_match = re.search(version_pattern, sheet_name)
        if version_match:
            version = version_match.group(1)
            # Remove everything after the last underscore (if present) and add version
            base_name = "_".join(sheet_name.split("_")[:-1]) if "_" in sheet_name else sheet_name
            sheet_name = f"{base_name}_{version}"

    # Ensure the sheet name is not longer than 31 characters
    if len(sheet_name) > 31:
        # If still too long, truncate while preserving the version number if present
        version_pattern = r"(.*)_([0-9]+\.[0-9]+[a-zA-Z]*)$"
        version_match = re.match(version_pattern, sheet_name)
        if version_match:
            base, version = version_match.groups()
            # Leave room for version plus underscore
            max_base_length = 31 - len(version) - 1
            sheet_name = f"{base[:max_base_length]}_{version}"
        else:
            sheet_name = sheet_name[:31]

    return sheet_name


def save_change_histories_to_excel(change_history_collection: dict[str, pd.DataFrame], output_path: Path) -> None:
    """
    Save the collected change histories to an Excel file.
    """
    # add timestamp to file name
    # there are two timestamps: one with datetime and another one with just date information.
    # It is handy during debugging to save different versions of the output files with the datetime information.
    # But in production we only want to save one file per day.
    # current_timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    current_timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    path_to_change_history_excel_file = output_path / f"{current_timestamp}_change_histories.xlsx"

    logger.info("💾 Saving change histories xlsx file %s", path_to_change_history_excel_file)

    # Define column widths (example: 20, 15, 30, etc.)
    column_widths = [6, 6, 46, 52, 52, 38, 15]  # Replace with your desired widths

    # Create a Pandas Excel writer using XlsxWriter as the engine
    # https://github.com/PyCQA/pylint/issues/3060 pylint: disable=abstract-class-instantiated
    with pd.ExcelWriter(path_to_change_history_excel_file, engine="xlsxwriter") as writer:
        for sheet_name, df in change_history_collection.items():
            shorten_sheet_name = extract_sheet_name(filename=sheet_name)
            df.to_excel(writer, sheet_name=shorten_sheet_name)

            # Access the XlsxWriter workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets[shorten_sheet_name]  # Use shortened name here

            # Create a text wrap format, this is needed to avoid the text being cut off in the cells
            wrap_format = workbook.add_format({"text_wrap": True})

            # Get the dimensions of the DataFrame
            (_, max_col) = df.shape

            assert max_col + 1 == len(column_widths)  # +1 cause of index

            # Apply text wrap format to each cell
            for col_num, width in enumerate(column_widths):
                worksheet.set_column(col_num, col_num, width, wrap_format)


def find_docx_files(input_path: Path) -> list[Path]:
    """
    Find all .docx files containing change histories.
    """
    docx_file_finder = DocxFileFinder.from_input_path(input_path=input_path)
    return docx_file_finder.get_all_docx_files_which_contain_change_histories()


def process_docx_file(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Read and process change history from a .docx file.
    """
    doc = docx.Document(str(file_path))
    logger.info("🤓 Start reading docx file '%s'", str(file_path))
    change_history_table = get_change_history_table(document=doc)

    if change_history_table is not None:
        change_history_table.sanitize_table()
        return change_history_table.table
    return None


def scrape_change_histories(input_path: Path, output_path: Path, format_version: EdifactFormatVersion) -> None:
    """
    starts the scraping process of the change histories
    """
    logger.info("👀 Start looking for change histories")
    path_to_files_with_changehistory = DocxFileFinder(
        path_to_edi_energy_mirror=input_path
    ).get_file_paths_for_change_history(format_version=format_version)

    change_history_collection = {}
    for file_path in path_to_files_with_changehistory:
        df = process_docx_file(file_path)
        if df is not None:
            change_history_collection[extract_sheet_name(file_path.name)] = df

    save_change_histories_to_excel(change_history_collection, output_path)
