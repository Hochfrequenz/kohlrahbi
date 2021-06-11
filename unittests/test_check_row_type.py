import docx
import pytest
from docx.shared import RGBColor

from check_row_type import RowType, define_row_type


class TestCheckRowType:
    @pytest.mark.parametrize(
        "text, left_indent_position, font_color, expected",
        [
            pytest.param("EDIFACT Struktur", 1905, RGBColor(0, 0, 0), RowType.HEADER, id="HEADER"),
            pytest.param(
                "Nachrichten-Kopfsegment", 1270, RGBColor(128, 128, 128), RowType.SEGMENTNAME, id="SEGMENTNAME"
            ),
            pytest.param("SG2", 1270, RGBColor(0, 0, 0), RowType.SEGMENTGRUPPE, id="SEGMENTGRUPPE"),
            pytest.param("UNH", 3810, RGBColor(0, 0, 0), RowType.SEGMENT, id="SEGMENT w/o Segmentgruppe"),
            pytest.param("SG2\tNAD", 1270, RGBColor(0, 0, 0), RowType.SEGMENT, id="SEGMENT w Segementgruppe"),
            pytest.param(
                "UNH\t0062", 3810, RGBColor(0, 0, 0), RowType.DATENELEMENT, id="DATENELEMENT w/o Segmentgruppe"
            ),
            pytest.param(
                "SG2\tNAD\t3035", 1270, RGBColor(0, 0, 0), RowType.DATENELEMENT, id="DATENELEMENT w Segementgruppe"
            ),
            pytest.param("", 635, RGBColor(0, 0, 0), RowType.EMPTY, id="EMPTY"),
        ],
    )
    def test_define_row_type(self, text: str, left_indent_position: int, font_color: RGBColor, expected: RowType):
        """Test if all defined row types are identified correctly.

        Args:
            text (str): Text content of the test cell
            left_indent_position (int): Position of the left indent in arbritrary units
            font_color (RGBColor): A class from docx to define colors
            expected (RowType): The expected RowType for each test case
        """
        # ! Attention: It seems that you can set the left indent to discret numbers!
        edifact_struktur_left_indent_position = 1270

        # create table test cell
        test_document = docx.Document()
        test_table = test_document.add_table(rows=1, cols=1)
        test_cell = test_table.add_row().cells[0]

        # insert text
        test_cell.text = text

        # set left indent positon
        test_cell.paragraphs[0].paragraph_format.left_indent = left_indent_position
        # set font color
        test_cell.paragraphs[0].runs[0].font.color.rgb = font_color

        result = define_row_type(
            edifact_struktur_cell=test_cell, left_indent_position=edifact_struktur_left_indent_position
        )
        assert result == expected
