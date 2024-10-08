"""
This module contains all tests regarding the AhbSubTable class
"""

from pathlib import Path

import docx
import pytest
from docx.table import Table

from kohlrahbi.ahbtable.ahbsubtable import AhbSubTable
from kohlrahbi.read_functions import get_ahb_table, get_all_paragraphs_and_tables
from kohlrahbi.unfoldedahb import UnfoldedAhb


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
        ahb_file_path: Path = Path.cwd() / Path(
            "unittests/test-edi-energy-mirror-repo/docx_files/UTILMD-11042-test.docx"
        )
        doc = docx.Document(str(ahb_file_path))  # Creating word reader object.
        all_paragraphs_and_tables = list(get_all_paragraphs_and_tables(parent=doc))

        # the first item in a word file seems to be always a paragraph. So we need the second item.
        docx_table = all_paragraphs_and_tables[1]

        if isinstance(docx_table, Table):
            ahb_sub_table = AhbSubTable.from_table_with_header(docx_table=docx_table)

            assert isinstance(ahb_sub_table, AhbSubTable)
        else:
            raise TypeError("You did not pass a docx table instance.")

    @pytest.mark.parametrize(
        "docx_path, segment_id, segment_code",
        [
            pytest.param(
                Path(__file__).parent
                / Path(
                    # pylint: disable=line-too-long
                    "test-files/docx_files/UTILMDAHBStrom-informatorischeLesefassung1.2aKonsolidierteLesefassungmitFehlerkorrekturenStand05.04.2024_99991231_20240405.docx"
                ),
                "00003",
                "UNH",
            ),
            pytest.param(
                Path(__file__).parent
                / Path(
                    # pylint: disable=line-too-long
                    "test-files/docx_files/UTILMDAHBStrom-informatorischeLesefassung1.2aKonsolidierteLesefassungmitFehlerkorrekturenStand05.04.2024_99991231_20240405.docx"
                ),
                "00004",
                "BGM",
            ),
            pytest.param(
                Path(__file__).parent
                / Path(
                    # pylint: disable=line-too-long
                    "test-files/docx_files/UTILMDAHBStrom-informatorischeLesefassung1.2aKonsolidierteLesefassungmitFehlerkorrekturenStand05.04.2024_99991231_20240405.docx"
                ),
                "00540",
                "UNT",
            ),
        ],
    )
    def test_segment_id_parsing(self, docx_path: Path, segment_id: str, segment_code: str) -> None:
        """
        https://github.com/Hochfrequenz/kohlrahbi/issues/304
        """
        assert docx_path.exists()
        doc = docx.Document(str(docx_path))  # Creating word reader object.
        ahb_table = get_ahb_table(document=doc, pruefi="55109")
        assert ahb_table is not None
        unfolded_ahb = UnfoldedAhb.from_ahb_table(ahb_table=ahb_table, pruefi="55109")
        assert unfolded_ahb is not None
        flat_ahb = unfolded_ahb.convert_to_flat_ahb()
        assert flat_ahb is not None
        assert any(l for l in flat_ahb.lines if l.segment_id is not None)
        assert any(l for l in flat_ahb.lines if l.segment_id == segment_id and l.segment_code == segment_code)
