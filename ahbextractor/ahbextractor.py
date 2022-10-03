"""
Main script of the AHB Extractor
"""
import sys
from pathlib import Path
from typing import List

import docx  # type:ignore[import]

from ahbextractor.helper.read_functions import get_ahb_extract


def main(file_paths: List[Path]) -> None:
    """
    Main function of the module ahbextractor.
    It reads the docx files and calls the function to extract all Prüfindentifikatoren tables.
    """
    for ahb_file_path in file_paths:
        print(f"Processing file {ahb_file_path}")
        output_directory_path = Path.cwd() / Path("output")
        if not output_directory_path.exists():
            output_directory_path.mkdir()
        xlsx_out_path = output_directory_path / Path("xlsx")
        if not xlsx_out_path.exists():
            xlsx_out_path.mkdir()
        path_to_all_in_one_excel = xlsx_out_path / Path(str(ahb_file_path.parts[-1])[:-5] + ".xls")

        # Remove old "all in one Excel file" if it already exists
        if path_to_all_in_one_excel.exists():
            path_to_all_in_one_excel.unlink(missing_ok=False)

        try:
            doc = docx.Document(ahb_file_path)  # Creating word reader object.

        except IOError as io_error:
            sys.exit(f"There was an error opening the file {ahb_file_path}: {io_error}")

        get_ahb_extract(document=doc, output_directory_path=output_directory_path, ahb_file_name=ahb_file_path)
