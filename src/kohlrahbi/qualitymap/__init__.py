"""
This module contains the functions to scrape the AHBs for quality maps.
"""

from pathlib import Path
from typing import Optional

import docx
import pandas as pd
from docx.document import Document
from docx.table import Table

from kohlrahbi.docxfilefinder import DocxFileFinder
from kohlrahbi.logger import logger
from kohlrahbi.qualitymap.qualitymaptable import QualityMapTable
from kohlrahbi.read_functions import get_all_paragraphs_and_tables


def find_docx_files(input_path: Path) -> list[Path]:
    """
    Find all .docx files containing change histories.
    """
    docx_file_finder = DocxFileFinder.from_input_path(input_path=input_path)
    return docx_file_finder.get_all_docx_files_which_contain_change_histories()


def is_quality_map_table(table: Table) -> bool:
    """
    Checks if the given table is quality map table.
    """
    try:
        return table.cell(row_idx=0, col_idx=0).text.strip() == "Änd-ID"
    except IndexError:
        return False


def get_quality_map_table(document: Document) -> Optional[QualityMapTable]:
    """
    Reads a docx file and extracts the quality map table.
    Returns None if no such table was found.
    """

    # Iterate through the whole word document
    logger.info("🔁 Start iterating through paragraphs and tables")
    for item in get_all_paragraphs_and_tables(parent=document):
        if isinstance(item, Table) and is_quality_map_table(table=item):
            change_history_table = QualityMapTable.from_docx_quality_map_table(docx_table=item)
            return change_history_table

    return None


def process_docx_file(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Read and process quality map from a .docx file.
    """
    doc = docx.Document(str(file_path))
    logger.info("🤓 Start reading docx file '%s'", str(file_path))
    quality_map_table = get_quality_map_table(document=doc)

    if quality_map_table is not None:
        # quality_map_table.sanitize_table()
        return quality_map_table.table
    return None


def scrape_quality_map(input_path: Path, output_path: Path) -> None:
    """
    starts the scraping process of the change histories
    """
    logger.info("👀 Start looking for change histories")
    ahb_file_paths = find_docx_files(input_path)

    # change_history_collection = {}
    for file_path in ahb_file_paths:
        df = process_docx_file(file_path)
        logger.info("Done with %s", file_path)
