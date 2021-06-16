"""
Main script of the AHB Extractor
"""

from pathlib import Path

import docx

from ahb_extractor.helper.read_functions import get_ahb_extract


def main():
    """
    Main function of the module ahb_extractor.
    It reads the docx file and calls the function to extract all infos.
    """

    input_directory_path = Path.cwd() / "documents"
    ahb_file_name = "UTILMD_AHB_WiM_3_1c_2021_04_01_2021_03_30.docx"
    path_to_ahb_file = input_directory_path / ahb_file_name

    output_directory_path = Path.cwd() / "output"
    path_to_all_in_one_excel = output_directory_path / "xlsx" / f"{ahb_file_name[:-5]}.xlsx"

    # Remove old "all in one excel file" if it already exists
    if path_to_all_in_one_excel.exists():
        path_to_all_in_one_excel.unlink(missing_ok=False)

    try:
        doc = docx.Document(path_to_ahb_file)  # Creating word reader object.

    except IOError:
        print("There was an error opening the file!")
        return

    get_ahb_extract(document=doc, output_directory_path=output_directory_path, ahb_file_name=ahb_file_name)


if __name__ == "__main__":
    main()
