import docx
import pytest

from unittests.cellparagraph import CellParagraph


@pytest.fixture
def get_ahb_table_with_multiple_paragraphs():
    def _setup_ahb_table(body_cell_paragraphs: list[CellParagraph]):
        doc = docx.Document()
        table = doc.add_table(rows=1, cols=1)

        body_cell = table.rows[0].cells[0]

        # the cell comes with an empty paragraph which I could not delete.
        # So we insert the BodyCellParagraph attributes into the empty paragraph
        first_body_cell_paragprah: CellParagraph = body_cell_paragraphs[0]

        body_cell.paragraphs[0].text = first_body_cell_paragprah.text

        if first_body_cell_paragprah.tabstop_positions is not None:
            for tabstop_position in first_body_cell_paragprah.tabstop_positions:
                body_cell.paragraphs[0].paragraph_format.tab_stops.add_tab_stop(tabstop_position)

        body_cell.paragraphs[0].paragraph_format.left_indent = first_body_cell_paragprah.left_indent_length

        for paragraph_index, bcp in zip(range(1, len(body_cell_paragraphs[1:]) + 1), body_cell_paragraphs[1:]):
            # add paragraph with text
            body_cell.add_paragraph(text=bcp.text)

            # set tabstop positions
            if bcp.tabstop_positions is not None:
                for tabstop_position in bcp.tabstop_positions:
                    body_cell.paragraphs[paragraph_index].paragraph_format.tab_stops.add_tab_stop(tabstop_position)

            # set left indent lenght
            body_cell.paragraphs[paragraph_index].paragraph_format.left_indent = bcp.left_indent_length

        return table

    return _setup_ahb_table
