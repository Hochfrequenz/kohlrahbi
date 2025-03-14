from pathlib import Path

import pandas as pd
import pytest

from kohlrahbi.ahbtable.ahbtable import AhbTable
from kohlrahbi.unfoldedahb import UnfoldedAhb


class TestAhbTable:
    """
    All tests regarding the AhbTable class
    """

    def test_append_ahb_sub_table(self):
        """
        Test appending of an AHB subtable
        """
        pass

    @pytest.mark.parametrize(
        "ahb_table_dataframe, expected_ahb_table_dataframe",
        [
            pytest.param(
                pd.DataFrame(
                    {
                        "Segment Gruppe": ["SG8", "Referenz auf die ID einer", "Messlokation", "SG8"],
                        "Segment": ["SEQ", "", "", ""],
                        "Datenelement": ["1229", "", "", ""],
                        "Codes und Qualifier": ["Z50", "", "", ""],
                        "Beschreibung": ["Messdatenregistriergerätedaten", "", "", ""],
                        "11042": ["", "", "", ""],
                        "11043": ["X", "", "", ""],
                        "11044": ["", "", "", ""],
                        "Bedingung": ["", "", "", ""],
                    }
                ),
                pd.DataFrame(
                    {
                        # note that the two fields in "Segment Gruppe" should be merged
                        # and the remaining artefact column should be dropped
                        "Segment Gruppe": ["SG8", "Referenz auf die ID einer Messlokation", "SG8"],
                        "Segment": ["SEQ", "", ""],
                        "Datenelement": ["1229", "", ""],
                        "Codes und Qualifier": ["Z50", "", ""],
                        "Beschreibung": ["Messdatenregistriergerätedaten", "", ""],
                        "11042": ["", "", ""],
                        "11043": ["X", "", ""],
                        "11044": ["", "", ""],
                        "Bedingung": ["", "", ""],
                    }
                ),
            )
        ],
    )
    def test_sanitize_ahb_table_dataframe(self, ahb_table_dataframe, expected_ahb_table_dataframe):
        """
        test the sanitize method of the AhbTable class
        """

        ahb_table = AhbTable(table=ahb_table_dataframe)

        ahb_table.sanitize()

        assert len(ahb_table.table) == len(expected_ahb_table_dataframe)
        assert ahb_table.table.equals(expected_ahb_table_dataframe)

    def test_sanitize_ahb_table_dataframe_44001(self):
        """
        test the sanitizing bug from https://github.com/Hochfrequenz/kohlrahbi/issues/140
        """
        df_file = Path(__file__).parent / "dataframes" / "44001_before_sanitizing.json"
        assert df_file.exists()
        df_table = pd.read_json(df_file)
        ahb_table = AhbTable(table=df_table)
        assert "E02" in ahb_table.table["Codes und Qualifier"].values
        assert "ZD2" in ahb_table.table["Codes und Qualifier"].values
        ahb_table.sanitize()
        assert "E02" in ahb_table.table["Codes und Qualifier"].values
        assert "ZD2" in ahb_table.table["Codes und Qualifier"].values
        unfolded_ahb = UnfoldedAhb.from_ahb_table(ahb_table=ahb_table, pruefi="44001")
        assert unfolded_ahb is not None
        for expected_transaktionsgrund, expected_beschreibung in [
            ("E01", "Ein-/Auszug (Umzug)"),
            ("E02", "Einzug in Neuanlage"),
            ("E03", "Wechsel"),
            ("ZD2", "Lieferbeginn undAbmeldung aus derErsatzversorgung"),
        ]:
            assert any(
                line
                for line in unfolded_ahb.unfolded_ahb_lines
                if line.segment_gruppe == "SG4"
                and line.segment == "STS"
                and line.datenelement == "9013"
                and line.code == expected_transaktionsgrund
                and line.beschreibung == expected_beschreibung
            ), f"No line with Transaktionsgrund '{expected_transaktionsgrund}' ({expected_beschreibung}) found"

    def test_fill_segement_gruppe_segement_dataelement(self):
        """
        test the fill_segement_gruppe_segement_dataelement method of the AhbTable class
        """
        example_dataframe = pd.DataFrame(
            {
                "Segment Gruppe": {
                    "0": "Nachrichten-Kopfsegment",
                    "1": "",
                    "2": "",
                    "3": "",
                    "4": "",
                    "5": "",
                    "6": "",
                    "7": "",
                    "8": "Beginn der Nachricht",
                    "9": "",
                    "10": "",
                    "11": "",
                    "12": "Nachrichtendatum",
                    "13": "",
                    "14": "",
                    "15": "",
                    "16": "",
                    "17": "MP-ID Absender",
                    "18": "SG2",
                    "19": "SG2",
                    "20": "SG2",
                    "21": "SG2",
                    "22": "SG2",
                    "23": "",
                    "24": "",
                    "25": "Ansprechpartner",
                },
                "Segment": {
                    "0": "",
                    "1": "UNH",
                    "2": "UNH",
                    "3": "UNH",
                    "4": "UNH",
                    "5": "UNH",
                    "6": "UNH",
                    "7": "UNH",
                    "8": "",
                    "9": "BGM",
                    "10": "BGM",
                    "11": "BGM",
                    "12": "",
                    "13": "DTM",
                    "14": "DTM",
                    "15": "DTM",
                    "16": "DTM",
                    "17": "",
                    "18": "",
                    "19": "NAD",
                    "20": "NAD",
                    "21": "NAD",
                    "22": "NAD",
                    "23": "",
                    "24": "",
                    "25": "",
                },
                "Datenelement": {
                    "0": "",
                    "1": "",
                    "2": "0062",
                    "3": "0065",
                    "4": "0052",
                    "5": "0054",
                    "6": "0051",
                    "7": "0057",
                    "8": "",
                    "9": "",
                    "10": "1001",
                    "11": "1004",
                    "12": "",
                    "13": "",
                    "14": "2005",
                    "15": "2380",
                    "16": "2379",
                    "17": "",
                    "18": "",
                    "19": "",
                    "20": "3035",
                    "21": "3039",
                    "22": "3055",
                    "23": "",
                    "24": "",
                    "25": "",
                },
                "Codes und Qualifier": {
                    "0": "",
                    "1": "",
                    "2": "Nachrichten-Referenznummer",
                    "3": "UTILMD",
                    "4": "D",
                    "5": "11A",
                    "6": "UN",
                    "7": "5.2e",
                    "8": "",
                    "9": "",
                    "10": "E01",
                    "11": "Dokumentennummer",
                    "12": "",
                    "13": "",
                    "14": "137",
                    "15": "Datum oder Uhrzeit oderZeitspanne, Wert",
                    "16": "303",
                    "17": "",
                    "18": "",
                    "19": "",
                    "20": "MS ",
                    "21": "MP-ID",
                    "22": "9",
                    "23": "293",
                    "24": "332",
                    "25": "",
                },
                "Beschreibung": {
                    "0": "",
                    "1": "",
                    "2": "",
                    "3": "Netzanschluss-Stammdaten",
                    "4": "Entwurfs-Version",
                    "5": "Ausgabe 2011 - A",
                    "6": "UN\\/CEFACT",
                    "7": "Versionsnummer derzugrundeliegendenBDEW-Nachrichtenbeschreibung",
                    "8": "",
                    "9": "",
                    "10": "Anmeldungen",
                    "11": "",
                    "12": "",
                    "13": "",
                    "14": "Dokumenten-\\/Nachrichtendatum\\/-zeit",
                    "15": "",
                    "16": "CCYYMMDDHHMMZZZ",
                    "17": "",
                    "18": "",
                    "19": "",
                    "20": "Dokumenten-\\/Nachrichtenausstellerbzw. -absender",
                    "21": "",
                    "22": "GS1",
                    "23": "DE, BDEW(Bundesverband derEnergie- undWasserwirtschaft e.V.)",
                    "24": "DE, DVGW Service &Consult GmbH",
                    "25": "",
                },
                "11042": {
                    "0": "",
                    "1": "Muss",
                    "2": "X",
                    "3": "X",
                    "4": "X",
                    "5": "X",
                    "6": "X",
                    "7": "X",
                    "8": "",
                    "9": "Muss",
                    "10": "X",
                    "11": "X",
                    "12": "",
                    "13": "Muss",
                    "14": "X",
                    "15": "X [931][494]",
                    "16": "X",
                    "17": "",
                    "18": "Muss",
                    "19": "Muss",
                    "20": "X",
                    "21": "X",
                    "22": "X",
                    "23": "X",
                    "24": "X",
                    "25": "",
                },
                "11043": {
                    "0": "",
                    "1": "Muss",
                    "2": "X",
                    "3": "X",
                    "4": "X",
                    "5": "X",
                    "6": "X",
                    "7": "X",
                    "8": "",
                    "9": "Muss",
                    "10": "X",
                    "11": "X",
                    "12": "",
                    "13": "Muss",
                    "14": "X",
                    "15": "X [931][494]",
                    "16": "X",
                    "17": "",
                    "18": "Muss",
                    "19": "Muss",
                    "20": "X",
                    "21": "X",
                    "22": "X",
                    "23": "X",
                    "24": "X",
                    "25": "",
                },
                "11044": {
                    "0": "",
                    "1": "Muss",
                    "2": "X",
                    "3": "X",
                    "4": "X",
                    "5": "X",
                    "6": "X",
                    "7": "X",
                    "8": "",
                    "9": "Muss",
                    "10": "X",
                    "11": "X",
                    "12": "",
                    "13": "Muss",
                    "14": "X",
                    "15": "X [931][494]",
                    "16": "X",
                    "17": "",
                    "18": "Muss",
                    "19": "Muss",
                    "20": "X",
                    "21": "X",
                    "22": "X",
                    "23": "X",
                    "24": "X",
                    "25": "",
                },
                "Bedingung": {
                    "0": "",
                    "1": "",
                    "2": "",
                    "3": "",
                    "4": "",
                    "5": "",
                    "6": "",
                    "7": "",
                    "8": "",
                    "9": "",
                    "10": "",
                    "11": "",
                    "12": "",
                    "13": "",
                    "14": "",
                    "15": "[494] Das hier genannte Datum muss der Zeitpunkt sein, zu dem das Dokument erstellt wurde, oder ein Zeitpunkt, der davor liegt  \\n[931] Format: ZZZ = +00",
                    "16": "",
                    "17": "",
                    "18": "",
                    "19": "",
                    "20": "",
                    "21": "",
                    "22": "",
                    "23": "",
                    "24": "",
                    "25": "",
                },
            }
        )

        expected_dataframe = pd.DataFrame(
            {
                "Segment Gruppe": {
                    "0": "Nachrichten-Kopfsegment",
                    "1": "Nachrichten-Kopfsegment",
                    "2": "Nachrichten-Kopfsegment",
                    "3": "Nachrichten-Kopfsegment",
                    "4": "Nachrichten-Kopfsegment",
                    "5": "Nachrichten-Kopfsegment",
                    "6": "Nachrichten-Kopfsegment",
                    "7": "Nachrichten-Kopfsegment",
                    "8": "Beginn der Nachricht",
                    "9": "Beginn der Nachricht",
                    "10": "Beginn der Nachricht",
                    "11": "Beginn der Nachricht",
                    "12": "Nachrichtendatum",
                    "13": "Nachrichtendatum",
                    "14": "Nachrichtendatum",
                    "15": "Nachrichtendatum",
                    "16": "Nachrichtendatum",
                    "17": "MP-ID Absender",
                    "18": "SG2",
                    "19": "SG2",
                    "20": "SG2",
                    "21": "SG2",
                    "22": "SG2",
                    "23": "SG2",
                    "24": "SG2",
                    "25": "Ansprechpartner",
                },
                "Segment": {
                    "0": "",
                    "1": "UNH",
                    "2": "UNH",
                    "3": "UNH",
                    "4": "UNH",
                    "5": "UNH",
                    "6": "UNH",
                    "7": "UNH",
                    "8": "",
                    "9": "BGM",
                    "10": "BGM",
                    "11": "BGM",
                    "12": "",
                    "13": "DTM",
                    "14": "DTM",
                    "15": "DTM",
                    "16": "DTM",
                    "17": "",
                    "18": "",
                    "19": "NAD",
                    "20": "NAD",
                    "21": "NAD",
                    "22": "NAD",
                    "23": "NAD",
                    "24": "NAD",
                    "25": "",
                },
                "Datenelement": {
                    "0": "",
                    "1": "",
                    "2": "0062",
                    "3": "0065",
                    "4": "0052",
                    "5": "0054",
                    "6": "0051",
                    "7": "0057",
                    "8": "",
                    "9": "0057",
                    "10": "1001",
                    "11": "1004",
                    "12": "",
                    "13": "1004",
                    "14": "2005",
                    "15": "2380",
                    "16": "2379",
                    "17": "",
                    "18": "",
                    "19": "2379",
                    "20": "3035",
                    "21": "3039",
                    "22": "3055",
                    "23": "3055",
                    "24": "3055",
                    "25": "",
                },
                "Codes und Qualifier": {
                    "0": "",
                    "1": "",
                    "2": "Nachrichten-Referenznummer",
                    "3": "UTILMD",
                    "4": "D",
                    "5": "11A",
                    "6": "UN",
                    "7": "5.2e",
                    "8": "",
                    "9": "",
                    "10": "E01",
                    "11": "Dokumentennummer",
                    "12": "",
                    "13": "",
                    "14": "137",
                    "15": "Datum oder Uhrzeit oderZeitspanne, Wert",
                    "16": "303",
                    "17": "",
                    "18": "",
                    "19": "",
                    "20": "MS ",
                    "21": "MP-ID",
                    "22": "9",
                    "23": "293",
                    "24": "332",
                    "25": "",
                },
                "Beschreibung": {
                    "0": "",
                    "1": "",
                    "2": "",
                    "3": "Netzanschluss-Stammdaten",
                    "4": "Entwurfs-Version",
                    "5": "Ausgabe 2011 - A",
                    "6": "UN\\/CEFACT",
                    "7": "Versionsnummer derzugrundeliegendenBDEW-Nachrichtenbeschreibung",
                    "8": "",
                    "9": "",
                    "10": "Anmeldungen",
                    "11": "",
                    "12": "",
                    "13": "",
                    "14": "Dokumenten-\\/Nachrichtendatum\\/-zeit",
                    "15": "",
                    "16": "CCYYMMDDHHMMZZZ",
                    "17": "",
                    "18": "",
                    "19": "",
                    "20": "Dokumenten-\\/Nachrichtenausstellerbzw. -absender",
                    "21": "",
                    "22": "GS1",
                    "23": "DE, BDEW(Bundesverband derEnergie- undWasserwirtschaft e.V.)",
                    "24": "DE, DVGW Service &Consult GmbH",
                    "25": "",
                },
                "11042": {
                    "0": "",
                    "1": "Muss",
                    "2": "X",
                    "3": "X",
                    "4": "X",
                    "5": "X",
                    "6": "X",
                    "7": "X",
                    "8": "",
                    "9": "Muss",
                    "10": "X",
                    "11": "X",
                    "12": "",
                    "13": "Muss",
                    "14": "X",
                    "15": "X [931][494]",
                    "16": "X",
                    "17": "",
                    "18": "Muss",
                    "19": "Muss",
                    "20": "X",
                    "21": "X",
                    "22": "X",
                    "23": "X",
                    "24": "X",
                    "25": "",
                },
                "11043": {
                    "0": "",
                    "1": "Muss",
                    "2": "X",
                    "3": "X",
                    "4": "X",
                    "5": "X",
                    "6": "X",
                    "7": "X",
                    "8": "",
                    "9": "Muss",
                    "10": "X",
                    "11": "X",
                    "12": "",
                    "13": "Muss",
                    "14": "X",
                    "15": "X [931][494]",
                    "16": "X",
                    "17": "",
                    "18": "Muss",
                    "19": "Muss",
                    "20": "X",
                    "21": "X",
                    "22": "X",
                    "23": "X",
                    "24": "X",
                    "25": "",
                },
                "11044": {
                    "0": "",
                    "1": "Muss",
                    "2": "X",
                    "3": "X",
                    "4": "X",
                    "5": "X",
                    "6": "X",
                    "7": "X",
                    "8": "",
                    "9": "Muss",
                    "10": "X",
                    "11": "X",
                    "12": "",
                    "13": "Muss",
                    "14": "X",
                    "15": "X [931][494]",
                    "16": "X",
                    "17": "",
                    "18": "Muss",
                    "19": "Muss",
                    "20": "X",
                    "21": "X",
                    "22": "X",
                    "23": "X",
                    "24": "X",
                    "25": "",
                },
                "Bedingung": {
                    "0": "",
                    "1": "",
                    "2": "",
                    "3": "",
                    "4": "",
                    "5": "",
                    "6": "",
                    "7": "",
                    "8": "",
                    "9": "",
                    "10": "",
                    "11": "",
                    "12": "",
                    "13": "",
                    "14": "",
                    "15": "[494] Das hier genannte Datum muss der Zeitpunkt sein, zu dem das Dokument erstellt wurde, oder ein Zeitpunkt, der davor liegt  \\n[931] Format: ZZZ = +00",
                    "16": "",
                    "17": "",
                    "18": "",
                    "19": "",
                    "20": "",
                    "21": "",
                    "22": "",
                    "23": "",
                    "24": "",
                    "25": "",
                },
            }
        )

        actual_ahb_table = AhbTable(table=example_dataframe)
        expected_ahb_table = AhbTable(table=expected_dataframe)

        actual_ahb_table.fill_segment_gruppe_segment_dataelement()

        # in case of debugging this test I can recommend the following command
        # diff = actual_ahb_table.table.eq(expected_ahb_table.table)
        # open the 'diff' dataframe in the data viewer of your IDE.
        # it shows a table with true and false values.
        # true if the field of the two dataframes at the same position are equal
        # and false if not.

        assert actual_ahb_table.table.equals(expected_ahb_table.table)

    def test_to_csv(self, tmp_path):
        """
        test the to_csv
        """
        ahb_table_dataframe = pd.DataFrame(
            {
                "Segment Gruppe": ["SG8", "Referenz auf die ID einer", "Messlokation", "SG8"],
                "Segment": ["SEQ", "", "", ""],
                "Datenelement": ["1229", "", "", ""],
                "Codes und Qualifier": ["Z50", "", "", ""],
                "Beschreibung": ["Messdatenregistriergerätedaten", "", "", ""],
                "11042": ["", "", "", ""],
                "11043": ["X", "", "", ""],
                "11044": ["", "", "", ""],
                "Bedingung": ["A", "B", "C", "D"],
            }
        )

        ahb_table = AhbTable(table=ahb_table_dataframe)

        ahb_table.sanitize()

        ahb_table.to_csv("11042", tmp_path / "actual-output" / "temp")

        assert (tmp_path / "actual-output" / "temp" / "csv" / "UTILMD" / "11042.csv").exists()

        with open(tmp_path / "actual-output" / "temp" / "csv" / "UTILMD" / "11042.csv", "r", encoding="utf-8") as file:
            actual_csv = file.read()
        expected_csv = ",Segment Gruppe,Segment,Datenelement,Codes und Qualifier,Beschreibung,11042,Bedingung\n0,SG8,SEQ,1229,Z50,Messdatenregistriergerätedaten,,A\n1,Referenz auf die ID einer,,,,,,B\n2,Messlokation,,,,,,C\n3,SG8,,,,,,D\n"
        assert actual_csv == expected_csv
