from pathlib import Path

import docx
import pytest  # type: ignore[import]
from docx.table import Table

from kohlrahbi.ahbsubtable import AhbSubTable
from kohlrahbi.helper.read_functions import get_all_paragraphs_and_tables


class TestAhbSubTable:
    """
    All tests regarding the AhbSubTable class
    """

    def test_from_table(self):
        """
        Test the instantiation of a AhbSubTable
        """
        ahb_file_path: Path = Path.cwd() / Path("unittests/docx_files/UTILMD-11042-test.docx")
        doc = docx.Document(ahb_file_path)  # Creating word reader object.
        all_paragraphs_and_tables = list(get_all_paragraphs_and_tables(parent=doc))

        docx_table = all_paragraphs_and_tables[
            1
        ]  # the first item in a word file seems to be always a paragraph. So we need the second item.

        if isinstance(docx_table, Table):
            ahb_sub_table = AhbSubTable.from_table_with_header(docx_table=docx_table)

            assert isinstance(ahb_sub_table, AhbSubTable)
        else:
            raise TypeError("You did not pass a docx table instance.")
