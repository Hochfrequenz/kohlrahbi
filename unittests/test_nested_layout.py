"""
Tests for AHB documents in the nested table layout (published by the BDEW since mid 2025).
"""

from pathlib import Path

import docx
import pytest
from docx.table import Table

from kohlrahbi.ahb import extract_pruefis_from_docx
from kohlrahbi.nestedlayout import is_nested_layout_table
from kohlrahbi.read_functions import (
    get_ahb_table,
    get_all_paragraphs_and_tables,
    is_last_row_end_of_message,
    table_header_starts_with_text_edifact_struktur,
)
from kohlrahbi.table_header import PruefiMetaData
from kohlrahbi.unfoldedahb import UnfoldedAhb

_test_files = Path(__file__).parent / "test-files"
_nested_layout_ahb = _test_files / "FV2610" / "AHB_ORDCHG_1.1_20261001_99991231_20261001_ooox_12179.docx"
_old_layout_ahb = (
    _test_files / "FV2310" / "COMDISAHB-informatorischeLesefassung1.0dKonsolidierteLesefassungmitFehlerkorrekturen"
    "Stand19.06.2023_20230719_20231001.docx"
)


def _get_ahb_tables(path: Path) -> list[Table]:
    document = docx.Document(str(path))
    return [
        item
        for item in get_all_paragraphs_and_tables(document)
        if isinstance(item, Table) and table_header_starts_with_text_edifact_struktur(item)
    ]


class TestNestedLayout:
    """
    Tests the parsing of AHB tables whose cells contain inner tables.
    """

    @pytest.mark.parametrize(
        "path, expected",
        [
            pytest.param(_nested_layout_ahb, True, id="nested layout"),
            pytest.param(_old_layout_ahb, False, id="old layout"),
        ],
    )
    def test_is_nested_layout_table(self, path: Path, expected: bool) -> None:
        tables = _get_ahb_tables(path)
        assert len(tables) > 0
        assert all(is_nested_layout_table(table) is expected for table in tables)

    def test_extract_pruefis(self) -> None:
        assert set(extract_pruefis_from_docx(_nested_layout_ahb)) == {"39000", "39001", "39002"}

    def test_metadata(self) -> None:
        ahb_table = get_ahb_table(docx.Document(str(_nested_layout_ahb)), "39001")
        assert ahb_table is not None
        assert ahb_table.metadata == [
            PruefiMetaData(
                pruefidentifikator="39000",
                name="Stornierung Sperr-/Entsperr- auftrag",
                communication_direction="LF an NB",
            ),
            PruefiMetaData(
                pruefidentifikator="39001",
                name="Weiterleitung der Stornierung",
                communication_direction="NB an MSB",
            ),
        ]

    def test_table_with_multiple_pruefis(self) -> None:
        ahb_table = get_ahb_table(docx.Document(str(_nested_layout_ahb)), "39000")
        assert ahb_table is not None
        table = ahb_table.table
        assert list(table.columns) == [
            "Segment Gruppe",
            "Segment",
            "Segment ID",
            "Datenelement",
            "Codes und Qualifier",
            "Beschreibung",
            "39000",
            "39001",
            "Bedingung",
        ]
        assert table.iloc[0].tolist() == ["Nachrichten-Kopfsegment"] + 8 * [""]
        assert table.iloc[1].tolist() == ["", "UNH", "00001", "", "", "", "Muss", "Muss", ""]
        # data elements without a code have their description in the code column (as for the old layout)
        assert table.iloc[2].tolist() == ["", "UNH", "", "0062", "Nachrichten-Referenznummer", "", "X", "X", ""]
        assert table.iloc[3].tolist() == ["", "UNH", "", "0065", "ORDCHG", "Bestelländerung", "X", "X", ""]

    def test_table_with_single_pruefi(self) -> None:
        """
        In tables with only one Prüfidentifikator, the cells with the expressions span over the middle column, too.
        """
        ahb_table = get_ahb_table(docx.Document(str(_nested_layout_ahb)), "39002")
        assert ahb_table is not None
        table = ahb_table.table
        assert table.columns[6] == "39002"
        assert table.iloc[1].tolist() == ["", "UNH", "00001", "", "", "", "Muss", ""]
        segment_rows = table[table["Segment ID"] != ""]
        assert (segment_rows["39002"] == "Muss").all()
        assert (segment_rows["Codes und Qualifier"] == "").all()

    def test_multiple_codes_and_bedingungen(self) -> None:
        ahb_table = get_ahb_table(docx.Document(str(_nested_layout_ahb)), "39002")
        assert ahb_table is not None
        rows = [row.tolist() for _, row in ahb_table.table.iterrows()]
        # each code of a data element is a row of its own
        assert ["SG3", "NAD", "", "3055", "9", "GS1", "X", ""] in rows
        assert [
            "",
            "",
            "",
            "",
            "293",
            "DE, BDEW (Bundesverband der Energie- und Wasserwirtschaft e.V.)",
            "X",
            "",
        ] in rows
        # the Bedingung texts are split at the condition keys
        dtm_row = next(row for row in rows if row[1] == "DTM" and row[3] == "2380")
        assert dtm_row[6] == "X [931] [494]"
        assert dtm_row[7].split("\n") == [
            "[494] Das hier genannte Datum muss der Zeitpunkt sein, zu dem das Dokument erstellt wurde, oder ein "
            "Zeitpunkt, der davor liegt.",
            "[931] Format: ZZZ = +00",
        ]

    def test_invisible_placeholders_are_ignored(self) -> None:
        for pruefi in ["39000", "39002"]:
            ahb_table = get_ahb_table(docx.Document(str(_nested_layout_ahb)), pruefi)
            assert ahb_table is not None
            assert not ahb_table.table.isin([".."]).any().any()

    def test_flat_ahb_uses_metadata_of_its_own_pruefi(self) -> None:
        """
        Prüfidentifikatoren that share a table must not get the description/direction of the first one.
        """
        ahb_table = get_ahb_table(docx.Document(str(_nested_layout_ahb)), "39001")
        assert ahb_table is not None
        flat_ahb = UnfoldedAhb.from_ahb_table(ahb_table=ahb_table, pruefi="39001").convert_to_flat_ahb()
        assert flat_ahb.meta.description == "Weiterleitung der Stornierung"
        assert flat_ahb.meta.direction == "NB an MSB"


@pytest.mark.parametrize(
    "last_cell_text, expected",
    [
        pytest.param("UNT\t0062", True, id="UNT"),
        pytest.param("UNZ\t0020", True, id="UNZ (MSCONS)"),
        pytest.param("UNT\t0074", False, id="not the last data element"),
        pytest.param("Sparte", False, id="other table"),
    ],
)
def test_is_last_row_end_of_message_old_layout(last_cell_text: str, expected: bool) -> None:
    table = docx.Document().add_table(rows=1, cols=2)
    table.cell(0, 0).text = last_cell_text
    assert is_last_row_end_of_message(table) is expected


def test_is_last_row_end_of_message_nested_layout() -> None:
    """the conditions of an AHB table must not be mixed with the texts of the tables after it"""
    tables = _get_ahb_tables(_nested_layout_ahb)
    assert all(is_last_row_end_of_message(table) for table in tables)
