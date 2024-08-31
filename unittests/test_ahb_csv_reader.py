from pathlib import Path
from typing import Dict, List, Optional

import pytest  # type:ignore[import]

from kohlrahbi.new_maus.flat_ahb_reader import FlatAhbCsvReader, check_file_can_be_parsed_as_ahb_csv


class TestAhbCsvReader:
    """
    Tests the ahb_csv_reader
    """

    @pytest.mark.parametrize(
        "field_names, expected_column_name",
        [
            pytest.param(
                [
                    "Segment Gruppe",
                    "Segment",
                    "Datenelement",
                    "Codes und Qualifier",
                    "Beschreibung",
                    "11042",
                    "Bedingung",
                ],
                "11042",
            ),
            pytest.param(["foo", "bar"], None),
            pytest.param(None, None),
            pytest.param([], None),
        ],
    )
    def test_ahb_expression_column_finder(self, field_names: list[str], expected_column_name: Optional[str]):
        actual = FlatAhbCsvReader._get_name_of_expression_column(field_names)
        assert actual == expected_column_name

    @pytest.mark.parametrize(
        "value, expected_is_value_pool_entry",
        [
            pytest.param(None, False),
            pytest.param("", False),
            pytest.param("E01", True),
            pytest.param("GABi-RLMoT", True),
            pytest.param("GABi-RLMmT", True),
            pytest.param("Gabi sitzt zu Hause ", False),
        ],
    )
    def test_is_value_pool_entry(self, value: Optional[str], expected_is_value_pool_entry: bool):
        actual = FlatAhbCsvReader._is_value_pool_entry(value)
        assert actual == expected_is_value_pool_entry

    @pytest.mark.parametrize(
        "value, expected_is_segment_group",
        [
            pytest.param(None, False),
            pytest.param("", False),
            pytest.param("Nachrichten-Endesegment", False),
            pytest.param("SG4", True),
            pytest.param("SG12", True),
        ],
    )
    def test_is_segment_group(self, value: Optional[str], expected_is_segment_group: bool):
        actual = FlatAhbCsvReader._is_segment_group(value)
        assert actual == expected_is_segment_group

    @pytest.mark.parametrize(
        "csv_code, csv_beschreibung, expected_code, expected_beschreibung",
        [
            pytest.param("Nachrichten-Referenznummer", None, None, "Nachrichten-Referenznummer"),
            pytest.param("137", "Dokumenten-/Nachrichtendatum/-zeit", "137", "Dokumenten-/Nachrichtendatum/-zeit"),
            pytest.param(
                "Datum oder Uhrzeit oderZeitspanne, Wert", None, None, "Datum oder Uhrzeit oderZeitspanne, Wert"
            ),
            pytest.param("303", "CCYYMMDDHHMMZZZ", "303", "CCYYMMDDHHMMZZZ"),
            pytest.param("9", "GS1", "9", "GS1"),
            pytest.param("IC", "Informationskontakt", "IC", "Informationskontakt"),
            pytest.param(
                "MS",
                "Dokumenten-/Nachrichtenausstellerbzw. -absender",
                "MS",
                "Dokumenten-/Nachrichtenausstellerbzw. -absender",
            ),
            pytest.param("TN", "Transaktions-Referenznummer", "TN", "Transaktions-Referenznummer"),
            pytest.param(
                "293",
                "DE, BDEW (Bundesverband der Energie- und Wasserwirtschaft e.V.)",
                "293",
                "DE, BDEW (Bundesverband der Energie- und Wasserwirtschaft e.V.)",
            ),
            pytest.param(
                "1.2",
                "Versionsnummer derzugrundeliegendenBDEW-Nachrichtenbeschreibung",
                "1.2",
                "Versionsnummer derzugrundeliegendenBDEW-Nachrichtenbeschreibung",
                id="format version reqote",
            ),
            pytest.param(
                "D",
                "Entwurfs-Version",
                "D",
                "Entwurfs-Version",
                id="entwurfs version reqote",
            ),
            pytest.param(
                "Dokumenten-/Nachrichtenausstellerbzw. -absender",
                "MS ",  # <-- has a trailing white space
                "MS",  # <-- has no trailing whitespace
                "Dokumenten-/Nachrichtenausstellerbzw. -absender",
                id="strip inputs; utilmd absender",
            ),
            pytest.param("EBD Nr. E_0456", "E_0456", "E_0456", "EBD Nr. E_0456", id="EBD Name in IFSTA"),
            pytest.param(
                "2.0d",
                "Versionsnummer derzugrundeliegendenBDEW-Nachrichtenbeschreibung",
                "2.0d",
                "Versionsnummer derzugrundeliegendenBDEW-Nachrichtenbeschreibung",
                id="iftsta version",
            ),
            pytest.param(
                "GABI-RLMNEV",
                "Nominierungsersatzverfahren - Exit (Hinweis: Dieser Code darf nur für Liefermonate vor dem 01.10.2016 genutzt werden)",
                "GABI-RLMNEV",
                "Nominierungsersatzverfahren - Exit (Hinweis: Dieser Code darf nur für Liefermonate vor dem 01.10.2016 genutzt werden)",
                id="GABI-RLMNEV",
            ),
            pytest.param(
                "GABI-RLMNEV",
                "Nominierungsersatzverfahren - Exit (Hinweis: Dieser Code darf nur für Liefermonate vor dem 01.10.2016 genutzt werden)",
                "GABI-RLMNEV",
                "Nominierungsersatzverfahren - Exit (Hinweis: Dieser Code darf nur für Liefermonate vor dem 01.10.2016 genutzt werden)",
                id="GABI-RLMNEV",
            ),
            pytest.param(
                "MS",
                "Nachrichtenaussteller bzw.",
                "MS",
                "Nachrichtenaussteller bzw.",
                id="MP-ID Absender REQOTE",
            ),
            pytest.param(
                "9",
                "GS1",
                "9",
                "GS1",
                id="Codeliste GS1",
            ),
            pytest.param(
                "E_0403",
                "EBD Nr. E_0403",
                "E_0403",
                "EBD Nr. E_0403",
                id="EBD E",
            ),
            pytest.param(
                "G_0009",
                "Codeliste Gas Nr. G_0009",
                "G_0009",
                "Codeliste Gas Nr. G_0009",
                id="EBD G",
            ),
            pytest.param(
                "MP-ID",
                None,
                None,
                "MP-ID",
                id="SG2 MP-ID",
            ),
            pytest.param(
                "MS",
                "Dokumenten-/Nachrichtenausstellerbzw. -absender",
                "MS",
                "Dokumenten-/Nachrichtenausstellerbzw. -absender",
                id="SG2 NAD+MS",
            ),
        ],
    )
    def test_code_description_separation(
        self,
        csv_code: Optional[str],
        csv_beschreibung: Optional[str],
        expected_code: Optional[str],
        expected_beschreibung: Optional[str],
    ):
        actual_code, actual_beschreibung = FlatAhbCsvReader.separate_value_pool_entry_and_name(
            csv_code, csv_beschreibung
        )
        assert actual_code == expected_code
        assert actual_beschreibung == expected_beschreibung

    def test_csv_file_reading_11042(self):
        path_to_csv: Path = Path(__file__).parents[1] / "unittests/ahbs/FV2204/UTILMD/11042.csv"
        reader = FlatAhbCsvReader(file_path=path_to_csv)
        assert len(reader.rows) == 844
        assert (
            len(
                [
                    r
                    for r in reader.rows
                    if r.section_name == "Korrespondenzanschrift des Kunden des Messstellenbetreibers"
                ]
            )
            > 0
        )  # this shows that the merging of sections spanning multiple lines works, see original CSV
        # first row assertions
        first_row = reader.rows[0]
        assert first_row.segment_code == "UNH"
        assert first_row.ahb_expression == "Muss"

        # last row assertions
        last_row = reader.rows[-1]
        assert last_row.segment_code == "UNT"
        assert last_row.data_element == "0062"
        assert last_row.name == "Nachrichten-Referenznummer"
        assert last_row.ahb_expression == "X"

        flat_ahb = reader.to_flat_ahb()
        assert len(flat_ahb.lines) < len(reader.rows)  # filter out the empty lines
        assert flat_ahb.get_segment_groups() == [None, "SG2", "SG3", "SG4", "SG5", "SG6", "SG8", "SG9", "SG10", "SG12"]
        assert all([line.index is not None for line in flat_ahb.lines]) is True

    @pytest.mark.parametrize(
        "input_lines,expected_lines",
        [
            pytest.param(
                [
                    {"": "0", "ASD": "asd"},
                    {"": "1", "Segment Gruppe": "Das ist der Anfang"},
                    {"": "2", "Segment Gruppe": "einer sehr langen"},
                    {"": "3", "Segment Gruppe": "Geschichte."},
                    {"": "4", "Foo": "Bar"},
                ],
                [
                    {"": "0", "ASD": "asd"},
                    {
                        "": "3",
                        "Segment Gruppe": "Das ist der Anfang einer sehr langen Geschichte.",
                        "Bedingung": "",
                        "Beschreibung": "",
                        "Codes und Qualifier": "",
                        "Datenelement": "",
                        "Segment": "",
                    },
                    {"": "4", "Foo": "Bar"},
                ],
            )
        ],
    )
    def test_merging_of_section_only_lines(self, input_lines: list[dict], expected_lines: list[dict]):
        actual = FlatAhbCsvReader.merge_section_only_lines(input_lines)
        assert actual == expected_lines

    def test_is_parsable(self):
        check_file_can_be_parsed_as_ahb_csv(Path(__file__).parents[1] / Path("unittests/ahbs/FV2204/UTILMD/11042.csv"))
        # if no exception is thrown, the test is successful

    @pytest.mark.parametrize(
        "candidate,expected",
        [
            pytest.param("[123] Foo Bar", {"123": "Foo Bar"}),
            pytest.param("[123] Foo Bar [456] Baz Bay", {"123": "Foo Bar", "456": "Baz Bay"}),
            pytest.param("[1] X [2] Y [3] Z", {"1": "X", "2": "Y", "3": "Z"}),
            pytest.param("", {}),
            pytest.param(None, {}),
        ],
    )
    def test_extract_bedingungen(self, candidate: str, expected: Dict[str, str]):
        actual = FlatAhbCsvReader._extract_bedingungen(candidate)
        assert actual == expected

    def test_extract_bedingungen_from_csv(self):
        path_to_csv: Path = Path(__file__).parents[1] / "unittests/ahbs/FV2204/UTILMD/11042.csv"
        reader = FlatAhbCsvReader(file_path=path_to_csv)
        actual = reader.extract_condition_texts()
        for key, value in actual.items():
            assert key.isnumeric()
            assert not value.isnumeric()
        # just two random checks
        assert actual["931"] == "Format: ZZZ = +00"
        assert (
            actual["621"]
            == "Hinweis: Es ist der MSB anzugeben, welcher ab dem Zeitpunkt der Lokation zugeordnet ist, der in DTM+76 (Datum zum geplanten Leistungsbeginn) genannt ist."
        )
