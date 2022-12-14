"""
Main script of the AHB Extractor
"""
from pathlib import Path
from typing import List

import docx  # type:ignore[import]

from kohlrahbi import logger
from kohlrahbi.helper.read_functions import get_kohlrahbi


def main(file_paths: List[Path]) -> None:
    """
    Main function of the module kohlrahbi.
    It reads the docx files and calls the function to extract all Prüfindentifikatoren tables.
    """
    for ahb_file_path in file_paths:
        logger.info("Processing file '%s'", ahb_file_path)
        output_directory_path = Path.cwd() / Path("output")
        output_directory_path.mkdir(exist_ok=True)
        xlsx_out_path = output_directory_path / Path("xlsx")
        xlsx_out_path.mkdir(exist_ok=True)
        path_to_all_in_one_excel = xlsx_out_path / Path(str(ahb_file_path.parts[-1])[:-5] + ".xls")

        # Remove old "all in one Excel file" if it already exists
        if path_to_all_in_one_excel.exists():
            path_to_all_in_one_excel.unlink(missing_ok=False)

        try:
            doc = docx.Document(ahb_file_path)  # Creating word reader object.

        except IOError:
            logger.exception("There was an error opening the file '%s'", ahb_file_path, exc_info=True)

        get_kohlrahbi(
            document=doc, output_directory_path=output_directory_path, ahb_file_name=ahb_file_path, pruefi="11010"
        )
