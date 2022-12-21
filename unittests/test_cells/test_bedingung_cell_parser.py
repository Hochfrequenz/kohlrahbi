import pytest
from docx.shared import Twips
import pandas as pd

from kohlrahbi.cells import BedingungCell
from unittests.cellparagraph import CellParagraph


class TestBedingungCell:
    @pytest.mark.parametrize(
        ["bedingung_cell_paragraph", "expected_dataframe"],
        [
            pytest.param(
                [
                    CellParagraph(
                        text="[494] Das hier genannte\nDatum muss der\nZeitpunkt sein, zu dem\ndas Dokument erstellt\nwurde, oder ein\nZeitpunkt, der davor liegt\n\n[931] Format: ZZZ = +00",
                        tabstop_positions=None,
                        left_indent_length=Twips(48),
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
                        "Bedingung": [
                            "[494] Das hier genannte Datum muss der Zeitpunkt sein, zu dem das Dokument erstellt wurde, oder ein Zeitpunkt, der davor liegt  \n[931] Format: ZZZ = +00"
                        ],
                    }
                ),
                id="11016 | 11017 | 11018: Nachrichten-Kopfsegment",
            ),
        ],
    )
    def test_edifact_struktur_cell_parser(
        self, get_ahb_table_with_multiple_paragraphs, bedingung_cell_paragraph, expected_dataframe
    ):

        table = get_ahb_table_with_multiple_paragraphs(body_cell_paragraphs=bedingung_cell_paragraph)

        bc: BedingungCell = BedingungCell(table_cell=table.row_cells(0)[0])

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
