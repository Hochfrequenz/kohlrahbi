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
    """
    # Remove .docx extension if present
    filename = filename.replace(".docx", "")

    # Handle standard AHB/MIG/EBD files
    parts = filename.split("_")
    if parts[0] in ["AHB", "MIG", "EBD"]:
        if parts[0] == "EBD":
            # EBD files have format: EBD_4.0b_date_...
            return f"{parts[0]}_{parts[1]}"
        # AHB/MIG files have format: AHB_COMDIS_1.0f_date_...
        return f"{parts[0]}_{parts[1]}_{parts[2]}"

    # Handle special cases
    if filename.startswith("allgemeinefestlegungeninformatorischelesefassung"):
        # Extract version if present
        version_pattern = r".*?_?([0-9]+\.[0-9]+[a-zA-Z]*)(?:_\d{8}|$)"
        version_match = re.search(version_pattern, filename)
        version = version_match.group(1) if version_match else ""
        return f"Allgemeine_Festlegungen_{version}"

    if filename.startswith("apiguidelineinformatorischelesefassung"):
        version_pattern = r".*?_?([0-9]+\.[0-9]+[a-zA-Z]*)(?:_\d{8}|$)"
        version_match = re.search(version_pattern, filename)
        version = version_match.group(1) if version_match else ""
        return f"API_Guideline_{version}"

    if filename.startswith("codeliste"):
        version_pattern = r".*?_?([0-9]+\.[0-9]+[a-zA-Z]*)(?:_\d{8}|$)"
        version_match = re.search(version_pattern, filename)
        version = version_match.group(1) if version_match else ""
        return f"CL_der_Konfigurationen_{version}"

    # Handle Entscheidungsbaum files
    if filename.startswith("Entscheidungsbaum"):
        version_pattern = r".*?([0-9]+\.[0-9]+)(?:_\d{8}|$)"
        version_match = re.search(version_pattern, filename)
        version = version_match.group(1) if version_match else ""
        return f"EBDs_CL_{version}"

    # For any other cases, just return the filename without extension
    # and ensure it's not longer than 31 characters
    return filename[:31]


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
        path_to_edi_energy_mirror=input_path, format_version=format_version
    ).get_file_paths_for_change_history()

    change_history_collection = {}
    for file_path in path_to_files_with_changehistory:
        df = process_docx_file(file_path)
        if df is not None:
            change_history_collection[extract_sheet_name(file_path.name)] = df

    save_change_histories_to_excel(change_history_collection, output_path)
