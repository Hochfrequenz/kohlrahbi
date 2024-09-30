from pathlib import Path
from typing import Optional

import docx
from docx.document import Document
from docx.table import Table

from kohlrahbi.docxfilefinder import DocxFileFinder
from kohlrahbi.logger import logger
from kohlrahbi.qualitymap.generator import generate_code
from kohlrahbi.qualitymap.qualitymaptable import QualityMapTable
from kohlrahbi.qualitymap.types import OutputFormat


def find_docx_files(input_path: Path) -> list[Path]:
    """
    Find all .docx files containing quality maps.
    """
    docx_file_finder = DocxFileFinder.from_input_path(input_path=input_path)
    return docx_file_finder.get_docx_files_which_contain_quality_map()


def is_quality_map_table(table: Table) -> bool:
    """
    Checks if the given table is quality map table.
    """
    try:
        return table.cell(row_idx=0, col_idx=0).text.strip() == "Qualität\n\nSegmentgruppe"
    except IndexError:
        return False


def get_quality_map_table(document: Document) -> Optional[QualityMapTable]:
    """
    Reads a docx file and extracts the quality map table.
    Returns None if no such table was found.
    """

    # Iterate through the whole word document
    logger.info("🔁 Start iterating through paragraphs and tables")
    for table in document.tables:
        if is_quality_map_table(table=table):
            change_history_table = QualityMapTable.from_docx_quality_map_table(docx_table=table)
            return change_history_table

    return None


def process_docx_file(file_path: Path) -> Optional[QualityMapTable]:
    """
    Read and process quality map from a .docx file.
    """
    doc = docx.Document(str(file_path))
    logger.info("🤓 Start reading docx file '%s'", str(file_path))
    quality_map_table = get_quality_map_table(document=doc)

    if quality_map_table is not None:
        return quality_map_table
    return None


def scrape_quality_map(input_path: Path, output_path: Path, output_format: OutputFormat) -> None:
    """
    starts the scraping process of the quality maps.

    Args:
        input_path (Path): The path to the input **directory** containing the docx files with quality maps.
        output_path (Path): The path to the output **directory** to save the scraped quality maps
        output_format (OutputFormat): The format in which the quality maps should be saved.
    """
    if input_path.is_dir() is False:
        logger.error("The input path '%s' is not a directory.", input_path)
        raise NotADirectoryError(f"The input path '{input_path}' is not a directory.")

    logger.info("👀 Start looking for quality maps")
    ahb_file_paths = find_docx_files(input_path)

    for file_path in ahb_file_paths:
        quality_map_table = process_docx_file(file_path)
        logger.info("Done with %s", file_path)
        if quality_map_table is None:
            logger.info("No quality map table found in %s", file_path)
            continue
        match output_format:
            case OutputFormat.CSV:
                quality_map_table.save_to_csv(output_path / Path(f"{file_path.stem}_quality_map.csv"))
            case OutputFormat.EXCEL:
                quality_map_table.save_to_xlsx(output_path / Path(f"{file_path.stem}_quality_map.xlsx"))
            case OutputFormat.C_SHARP_EXTRACT:
                code = generate_code(quality_map_table)
                with open(output_path / Path(f"{file_path.stem}_quality_map.cs"), "w", encoding="utf-8") as file:
                    file.write(code)
