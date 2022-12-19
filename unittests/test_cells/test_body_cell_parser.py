import docx
import pytest
from docx.shared import Twips
import pandas as pd

from kohlrahbi.cells import BodyCell
from unittests.conftest import left_indent_length
from unittests.bodycellparagraph import BodyCellParagraph


class TestBodyCell:
    """
    This test class contains all tests of the BodyCell class
    """

    @pytest.mark.parametrize(
        ["cell_text", "tabstop_positions", "expected_dataframe"],
        [
            pytest.param(
                "Nachrichten-Referenznummer\tX\tX\tX",
                [Twips(3088), Twips(4064), Twips(5026)],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": [""],
                        "Datenelement": [""],
                        "Codes und Qualifier": ["Nachrichten-Referenznummer"],
                        "Beschreibung": [""],
                        "11016": ["X"],
                        "11017": ["X"],
                        "11018": ["X"],
                    }
                ),
                id="11016 | 11017 | 11018: Qualifier - Nachrichten-Referenznummer",
            ),
            pytest.param(
                "UN\tUN/CEFACT\tX\tX\tX",
                [Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": [""],
                        "Datenelement": [""],
                        "Codes und Qualifier": ["UN"],
                        "Beschreibung": ["UN/CEFACT"],
                        "11016": ["X"],
                        "11017": ["X"],
                        "11018": ["X"],
                    }
                ),
                id="11016 | 11017 | 11018: Code - UN",
            ),
            pytest.param(
                "93\tDatum Vertragsende\tX\tX",
                [Twips(693), Twips(3088), Twips(4064)],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": [""],
                        "Datenelement": [""],
                        "Codes und Qualifier": ["93"],
                        "Beschreibung": ["Datum Vertragsende"],
                        "11016": ["X"],
                        "11017": ["X"],
                        "11018": [""],
                    }
                ),
                id="11016 | 11017: Code - 93 - only two X",
            ),
            pytest.param(
                "157\tGültigkeit, Beginndatum\tX",
                [Twips(693), Twips(5026)],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": [""],
                        "Datenelement": [""],
                        "Codes und Qualifier": ["157"],
                        "Beschreibung": ["Gültigkeit, Beginndatum"],
                        "11016": [""],
                        "11017": [""],
                        "11018": ["X"],
                    }
                ),
                id="11018: Code - 157 - only one X",
            ),
            pytest.param(
                "E_0400\tEBD Nr. E_0400\tX [492]\tX [492]",
                [Twips(693), Twips(4064), Twips(5026)],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": [""],
                        "Datenelement": [""],
                        "Codes und Qualifier": ["E_0400"],
                        "Beschreibung": ["EBD Nr. E_0400"],
                        "11016": [""],
                        "11017": ["X [492]"],
                        "11018": ["X [492]"],
                    }
                ),
                id="11017 | 11018: Code - E_0400 - X with condition",
            ),
        ],
    )
    def test_body_cell_parse_with_one_line(
        self,
        get_ahb_table_with_single_paragraph,
        cell_text: str,
        tabstop_positions: list[Twips],
        expected_dataframe: pd.DataFrame,
    ):

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

        table = get_ahb_table_with_single_paragraph(cell_text, tabstop_positions)

        indicator_tabstop_positions: list[int] = [Twips(693), Twips(3088), Twips(4064), Twips(5026)]

        bc: BodyCell = BodyCell(
            table_cell=table.row_cells(0)[0],
            left_indent_position=left_indent_length,
            indicator_tabstop_positions=indicator_tabstop_positions,
        )

        df = bc.parse(ahb_row_dataframe=empty_ahb_row)

        assert df.equals(expected_dataframe)

    def test_body_cell_parse_with_multiple_lines(self, get_ahb_table_with_multiple_paragraphs):
        expexted_df = pd.DataFrame(
            {
                "Segment Gruppe": ["", "", ""],
                "Segment": ["", "", ""],
                "Datenelement": ["", "", ""],
                "Codes und Qualifier": ["EM", "FX", "TE"],
                "Beschreibung": ["Elektronische Post", "Telefax", "Telefon"],
                "11016": ["X [1P0..1]", "X [1P0..1]", "X [1P0..1]"],
                "11017": ["X [1P0..1]", "X [1P0..1]", "X [1P0..1]"],
                "11018": ["X [1P0..1]", "X [1P0..1]", "X [1P0..1]"],
            }
        )

        body_cell_paragraphs: list[BodyCellParagraph] = [
            BodyCellParagraph(
                text="EM\tElektronische Post\tX [1P0..1]\tX [1P0..1]\tX [1P0..1]",
                tabstop_positions=[Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                left_indent_length=Twips(693),
            ),
            BodyCellParagraph(
                text="FX\tTelefax\tX [1P0..1]\tX [1P0..1]\tX [1P0..1]",
                tabstop_positions=[Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                left_indent_length=Twips(693),
            ),
            BodyCellParagraph(
                text="TE\tTelefon\tX [1P0..1]\tX [1P0..1]\tX [1P0..1]",
                tabstop_positions=[Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                left_indent_length=Twips(693),
            ),
        ]

        table = get_ahb_table_with_multiple_paragraphs(body_cell_paragraphs=body_cell_paragraphs)

        indicator_tabstop_positions: list[int] = [Twips(693), Twips(3088), Twips(4064), Twips(5026)]

        bc: BodyCell = BodyCell(
            table_cell=table.row_cells(0)[0],
            left_indent_position=left_indent_length,
            indicator_tabstop_positions=indicator_tabstop_positions,
        )

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

        df = bc.parse(ahb_row_dataframe=empty_ahb_row)

        assert df.equals(expexted_df)

        print()
