"""
This module contains all tests regarding the AhbSubTable class
"""

from pathlib import Path

import docx  # type:ignore[import]
from docx.table import Table  # type:ignore[import]

from kohlrahbi.ahbtable.ahbsubtable import AhbSubTable
from kohlrahbi.read_functions import get_all_paragraphs_and_tables


class TestAhbSubTable:
    """
    All tests regarding the AhbSubTable class
    """

    def test_from_table(self) -> None:
        """
        Test the instantiation of a AhbSubTable

        This method tests the instantiation of an AhbSubTable object by creating a word reader object,
        extracting the table from the document, and checking if the resulting object is an instance of AhbSubTable.

        Raises:
            TypeError: If the input is not a docx table instance.
        """
        ahb_file_path: Path = Path.cwd() / Path("unittests/test-files/docx_files/UTILMD-11042-test.docx")
        doc = docx.Document(str(ahb_file_path))  # Creating word reader object.
        all_paragraphs_and_tables = list(get_all_paragraphs_and_tables(parent=doc))

        # the first item in a word file seems to be always a paragraph. So we need the second item.
        docx_table = all_paragraphs_and_tables[1]

        if isinstance(docx_table, Table):
            ahb_sub_table = AhbSubTable.from_table_with_header(docx_table=docx_table)

            assert isinstance(ahb_sub_table, AhbSubTable)
        else:
            raise TypeError("You did not pass a docx table instance.")
