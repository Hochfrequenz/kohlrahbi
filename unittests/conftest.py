import pytest
from docx.shared import Length, Twips
import docx
import pandas as pd

left_indent_length: Length = Twips(693)

empty_ahb_row: pd.DataFrame = pd.DataFrame(
    {
        "Segment Gruppe": [""],
        "Segment": [""],
        "Datenelement": [""],
        "Codes und Qualifier": [""],
        "Beschreibung": [""],
        "11016": [""],
        "11017": [""],
        "11018": [""],
    }
)


@pytest.fixture
def create_ahb_table():
    def _setup_ahb_table(cell_text: str, tabstop_positions: list[Length]):

        doc = docx.Document()
        table = doc.add_table(rows=1, cols=1)

        body_cell = table.rows[0].cells
        body_cell[0].text = cell_text

        for tabstop_position in tabstop_positions:
            body_cell[0].paragraphs[0].paragraph_format.tab_stops.add_tab_stop(tabstop_position)

        body_cell[0].paragraphs[0].paragraph_format.left_indent = left_indent_length

        return table

    return _setup_ahb_table
