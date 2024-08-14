import pandas as pd
import pytest
from docx.shared import Twips

from kohlrahbi.docxtablecells import EdifactStrukturCell
from unittests.cellparagraph import CellParagraph


class TestEdifactStrukturCell:
    @pytest.mark.parametrize(
        ["edifact_struktur_cell_paragraph", "expected_dataframe"],
        [
            pytest.param(
                [
                    CellParagraph(
                        text="Nachrichten-Kopfsegment",
                        tabstop_positions=None,
                        left_indent_length=Twips(581),
                    ),
                ],
                pd.DataFrame(
                    {
                        "Segment Gruppe": ["Nachrichten-Kopfsegment"],
                        "Segment": [""],
                        "Datenelement": [""],
                        "Segment ID": [""],
                        "Codes und Qualifier": [""],
                        "Beschreibung": [""],
                        "11016": [""],
                        "11017": [""],
                        "11018": [""],
                        "Bedingung": [""],
                    }
                ),
                id="11016 | 11017 | 11018: Nachrichten-Kopfsegment",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="UNH",
                        tabstop_positions=None,
                        left_indent_length=Twips(64),
                    ),
                ],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": ["UNH"],
                        "Datenelement": [""],
                        "Segment ID": [""],
                        "Codes und Qualifier": [""],
                        "Beschreibung": [""],
                        "11016": [""],
                        "11017": [""],
                        "11018": [""],
                        "Bedingung": [""],
                    }
                ),
                id="11016 | 11017 | 11018: UNH",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="UNH\tR0003",
                        tabstop_positions=[Twips(128)],
                        left_indent_length=Twips(64),
                    ),
                ],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": ["UNH"],
                        "Datenelement": [""],
                        "Segment ID": ["R0003"],
                        "Codes und Qualifier": [""],
                        "Beschreibung": [""],
                        "11016": [""],
                        "11017": [""],
                        "11018": [""],
                        "Bedingung": [""],
                    }
                ),
                id="11016 | 11017 | 11018: UNH",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="UNH\t0062",
                        tabstop_positions=[Twips(128)],  # these tabstops are made up!
                        left_indent_length=Twips(64),
                    ),
                ],
                pd.DataFrame(
                    {
                        "Segment Gruppe": [""],
                        "Segment": ["UNH"],
                        "Datenelement": ["0062"],
                        "Segment ID": [""],
                        "Codes und Qualifier": [""],
                        "Beschreibung": [""],
                        "11016": [""],
                        "11017": [""],
                        "11018": [""],
                        "Bedingung": [""],
                    }
                ),
                id="11016 | 11017 | 11018: UNH - 0062",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="SG2\tNAD\t3035",
                        tabstop_positions=[Twips(128), Twips(256)],  # these tabstops are made up!
                        left_indent_length=Twips(581),
                    ),
                ],
                pd.DataFrame(
                    {
                        "Segment Gruppe": ["SG2"],
                        "Segment": ["NAD"],
                        "Datenelement": ["3035"],
                        "Segment ID": [""],
                        "Codes und Qualifier": [""],
                        "Beschreibung": [""],
                        "11016": [""],
                        "11017": [""],
                        "11018": [""],
                        "Bedingung": [""],
                    }
                ),
                id="11016 | 11017 | 11018: SG2 - NAD - 3035",
            ),
            pytest.param(
                [
                    CellParagraph(
                        text="SG2\tNAD\t3035",
                        tabstop_positions=[Twips(128), Twips(256)],  # these tabstops are made up!
                        left_indent_length=Twips(581),
                    ),
                ],
                pd.DataFrame(
                    {
                        "Segment Gruppe": ["SG2"],
                        "Segment": ["NAD"],
                        "Datenelement": ["3035"],
                        "Segment ID": [""],
                        "Codes und Qualifier": [""],
                        "Beschreibung": [""],
                        "11016": [""],
                        "11017": [""],
                        "11018": [""],
                        "Bedingung": [""],
                    }
                ),
                id="11016 | 11017 | 11018: SG2 - NAD - 3035",
            ),
        ],
    )
    def test_edifact_struktur_cell_parser(
        self, get_ahb_table_with_multiple_paragraphs, edifact_struktur_cell_paragraph, expected_dataframe
    ) -> None:
        table = get_ahb_table_with_multiple_paragraphs(body_cell_paragraphs=edifact_struktur_cell_paragraph)

        esc: EdifactStrukturCell = EdifactStrukturCell(
            table_cell=table.row_cells(0)[0], edifact_struktur_cell_left_indent_position=Twips(64)
        )

        empty_ahb_row: pd.DataFrame = pd.DataFrame(
            {
                "Segment Gruppe": [""],
                "Segment": [""],
                "Datenelement": [""],
                "Segment ID": [""],
                "Codes und Qualifier": [""],
                "Beschreibung": [""],
                "11016": [""],
                "11017": [""],
                "11018": [""],
                "Bedingung": [""],
            }
        )

        df = esc.parse(ahb_row_dataframe=empty_ahb_row)

        assert df.equals(expected_dataframe)
