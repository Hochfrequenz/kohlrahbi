from pathlib import Path

import docx

from ahb_extractor.helper.read_functions import get_ahb_extract


def main():

    input_directory_path = Path.cwd() / "documents"
    ahb_file_name = "UTILMD_AHB_WiM_3_1c_2021_04_01_2021_03_30.docx"
    path_to_ahb_file = input_directory_path / ahb_file_name

    output_directory_path = Path.cwd() / "output"

    try:
        doc = docx.Document(path_to_ahb_file)  # Creating word reader object.

    except IOError:
        print("There was an error opening the file!")
        return

    get_ahb_extract(document=doc, output_directory_path=output_directory_path, ahb_file_name=ahb_file_name)


if __name__ == "__main__":
    main()
