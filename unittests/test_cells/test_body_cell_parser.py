import pandas as pd
import pytest
from docx.shared import Length, Twips

from kohlrahbi.docxtablecells import BodyCell
from unittests.cellparagraph import CellParagraph

left_indent_length: Length = Twips(64)


class TestBodyCell:
    """
    This test class contains all tests of the BodyCell class
    """

    @pytest.mark.parametrize(
        ["body_cell_paragraphs", "expected_dataframe"],
        [
            pytest.param(
                [
                    CellParagraph(
                        text="Nachrichten-Referenznummer\tX\tX\tX",
                        tabstop_positions=[Twips(3088), Twips(4064), Twips(5026)],
                        left_indent_length=Twips(64),
                    ),
                ],
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
                        "Bedingung": [""],
                    }
                ),
                id="11016 | 11017 | 11018: Qualifier - Nachrichten-Referenznummer",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="UN\tUN/CEFACT\tX\tX\tX",
                        tabstop_positions=[Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                        left_indent_length=Twips(64),
                    ),
                ],
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
                        "Bedingung": [""],
                    }
                ),
                id="11016 | 11017 | 11018: Code - UN",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="93\tDatum Vertragsende\tX\tX",
                        tabstop_positions=[Twips(693), Twips(3088), Twips(4064)],
                        left_indent_length=Twips(64),
                    )
                ],
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
                        "Bedingung": [""],
                    }
                ),
                id="11016 | 11017: Code - 93 - only two X",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="157\tGültigkeit, Beginndatum\tX",
                        tabstop_positions=[Twips(693), Twips(5026)],
                        left_indent_length=Twips(64),
                    )
                ],
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
                        "Bedingung": [""],
                    }
                ),
                id="11018: Code - 157 - only one X",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="E_0400\tEBD Nr. E_0400\tX [492]\tX [492]",
                        tabstop_positions=[Twips(693), Twips(4064), Twips(5026)],
                        left_indent_length=Twips(64),
                    )
                ],
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
                        "Bedingung": [""],
                    }
                ),
                id="11017 | 11018: Code - E_0400 - X with condition",
            ),
        ],
    )
    def test_body_cell_parse_with_one_line(
        self, get_ahb_table_with_multiple_paragraphs, body_cell_paragraphs, expected_dataframe
    ) -> None:
        table = get_ahb_table_with_multiple_paragraphs(body_cell_paragraphs=body_cell_paragraphs)

        indicator_tabstop_positions: list[int] = [Twips(693), Twips(3088), Twips(4064), Twips(5026)]

        bc: BodyCell = BodyCell(
            table_cell=table.row_cells(0)[0],
            left_indent_position=Twips(64),
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
                "Bedingung": [""],
            }
        )

        df = bc.parse(ahb_row_dataframe=empty_ahb_row)

        assert df.equals(expected_dataframe)

    @pytest.mark.parametrize(
        ["body_cell_paragraphs", "empty_ahb_row", "expected_dataframe"],
        [
            pytest.param(
                [
                    CellParagraph(
                        text="EM\tElektronische Post\tX [1P0..1]\tX [1P0..1]\tX [1P0..1]",
                        tabstop_positions=[Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                        left_indent_length=Twips(64),
                    ),
                    CellParagraph(
                        text="FX\tTelefax\tX [1P0..1]\tX [1P0..1]\tX [1P0..1]",
                        tabstop_positions=[Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                        left_indent_length=Twips(64),
                    ),
                    CellParagraph(
                        text="TE\tTelefon\tX [1P0..1]\tX [1P0..1]\tX [1P0..1]",
                        tabstop_positions=[Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                        left_indent_length=Twips(64),
                    ),
                ],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": [""],
                        "Datenelement": [""],
                        "Codes und Qualifier": [""],
                        "Beschreibung": [""],
                        "11016": [""],
                        "11017": [""],
                        "11018": [""],
                        "Bedingung": [""],
                    }
                ),
                pd.DataFrame(
                    {
                        "Segment Gruppe": ["", "", ""],
                        "Segment": ["", "", ""],
                        "Datenelement": ["", "", ""],
                        "Codes und Qualifier": ["EM", "FX", "TE"],
                        "Beschreibung": ["Elektronische Post", "Telefax", "Telefon"],
                        "11016": ["X [1P0..1]", "X [1P0..1]", "X [1P0..1]"],
                        "11017": ["X [1P0..1]", "X [1P0..1]", "X [1P0..1]"],
                        "11018": ["X [1P0..1]", "X [1P0..1]", "X [1P0..1]"],
                        "Bedingung": ["", "", ""],
                    }
                ),
                id="11016 | 11017 | 11018: SG3 COM 3155",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="9\tGS1\tX\tX\tX",
                        tabstop_positions=[Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                        left_indent_length=Twips(64),
                    ),
                    CellParagraph(
                        text="293\tDE, BDEW\tX\tX\tX",
                        tabstop_positions=[Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                        left_indent_length=Twips(64),
                    ),
                    CellParagraph(
                        text="(Bundesverband der",
                        tabstop_positions=[],
                        left_indent_length=Twips(693),
                    ),
                    CellParagraph(
                        text="Energie- und",
                        tabstop_positions=[],
                        left_indent_length=Twips(693),
                    ),
                    CellParagraph(
                        text="Wasserwirtschaft e.V.)",
                        tabstop_positions=[],
                        left_indent_length=Twips(693),
                    ),
                    CellParagraph(
                        text="332\tDE, DVGW Service &\tX\tX\tX",
                        tabstop_positions=[Twips(693), Twips(3088), Twips(4064), Twips(5026)],
                        left_indent_length=Twips(64),
                    ),
                    CellParagraph(
                        text="Consult GmbH",
                        tabstop_positions=[],
                        left_indent_length=Twips(693),
                    ),
                ],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": [""],
                        "Datenelement": [""],
                        "Codes und Qualifier": [""],
                        "Beschreibung": [""],
                        "11016": [""],
                        "11017": [""],
                        "11018": [""],
                        "Bedingung": [""],
                    }
                ),
                pd.DataFrame(
                    {
                        "Segment Gruppe": ["", "", ""],
                        "Segment": ["", "", ""],
                        "Datenelement": ["", "", ""],
                        "Codes und Qualifier": ["9", "293", "332"],
                        "Beschreibung": [
                            "GS1",
                            "DE, BDEW(Bundesverband derEnergie- undWasserwirtschaft e.V.)",
                            "DE, DVGW Service &Consult GmbH",
                        ],
                        "11016": ["X", "X", "X"],
                        "11017": ["X", "X", "X"],
                        "11018": ["X", "X", "X"],
                        "Bedingung": ["", "", ""],
                    }
                ),
                id="11016 | 11017 | 11018: SG2 NAD 3055",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="ORDER\tBestellung\tX",
                        tabstop_positions=[Twips(693), Twips(3088)],
                        left_indent_length=Twips(64),
                    ),
                    CellParagraph(
                        text="S",
                        tabstop_positions=[],
                        left_indent_length=Twips(64),
                    ),
                ],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": [""],
                        "Datenelement": [""],
                        "Codes und Qualifier": [""],
                        "Beschreibung": [""],
                        "17001": [""],
                        "Bedingung": [""],
                    }
                ),
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": [""],
                        "Datenelement": [""],
                        "Codes und Qualifier": ["ORDERS"],
                        "Beschreibung": ["Bestellung"],
                        "17001": ["X"],
                        "Bedingung": [""],
                    }
                ),
                id="17001: - UNH 0065 ORDERS",
            ),
        ],
    )
    def test_body_cell_parse_with_multiple_lines(
        self, get_ahb_table_with_multiple_paragraphs, body_cell_paragraphs, empty_ahb_row, expected_dataframe
    ) -> None:
        table = get_ahb_table_with_multiple_paragraphs(body_cell_paragraphs=body_cell_paragraphs)

        indicator_tabstop_positions: list[int] = [Twips(693), Twips(3088), Twips(4064), Twips(5026)]

        bc: BodyCell = BodyCell(
            table_cell=table.row_cells(0)[0],
            left_indent_position=Twips(64),
            indicator_tabstop_positions=indicator_tabstop_positions,
        )

        df = bc.parse(ahb_row_dataframe=empty_ahb_row)

        assert df.equals(expected_dataframe)
