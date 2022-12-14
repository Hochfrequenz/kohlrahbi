import docx
import pytest
from docx.shared import Inches

from kohlrahbi.parser import middle_cell_parser


class TestMiddleCellParser:
    """
    This test class collects all tests in context of the middle cell parser
    """

    @pytest.mark.parametrize(
        ["left_indent_position", "expected_result"],
        [
            pytest.param(Inches(1), True, id="Paragraph contains code"),
            pytest.param(Inches(4), False, id="Paragraph does NOT contains code"),
        ],
    )
    def test_does_paragraph_contain_qualifier_or_code(self, left_indent_position, expected_result):
        doc = docx.Document()
        test_paragraph = doc.add_paragraph("\tMuss\tMuss\tMuss")
        test_paragraph.paragraph_format.left_indent = Inches(1)
        # though it feels weird to use Inches, stick to it! I tried to use the length class Mm()
        # but there was always a difference between:
        #   absolute_length = Mm(1)
        #   test_paragraph.paragraph_format.left_indent = Mm(1)
        #   absolute_length != test_paragraph.paragraph_format.left_indent
        # but I don't know why ...

        assert (
            middle_cell_parser.does_paragraph_contain_qualifier_or_code(
                paragraph=test_paragraph, left_indent_position=left_indent_position
            )
            is expected_result
        )

    def test_has_paragraph_tabstops(self):
        doc = docx.Document()
        test_paragraph = doc.add_paragraph("\tMuss\tMuss\tMuss")
        test_paragraph.paragraph_format.tab_stops.add_tab_stop(Inches(0.5))

        assert middle_cell_parser.has_paragraph_tabstops(paragraph=test_paragraph)

    def test_parse_middle_cell(self):
        records = ((3, "101", "Spam"), (7, "422", "Eggs"), (4, "631", "Spam, spam, eggs, and spam"))

        doc = docx.Document()
        table = doc.add_table(rows=1, cols=3)
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Qty"
        hdr_cells[1].text = "Id"
        hdr_cells[2].text = "Desc"
        for qty, id, desc in records:
            row_cells = table.add_row().cells
            row_cells[0].text = str(qty)
            row_cells[1].text = id
            row_cells[2].text = desc
