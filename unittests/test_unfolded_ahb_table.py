from maus.edifact import EdifactFormat
from maus.models.anwendungshandbuch import AhbLine, AhbMetaInformation, FlatAnwendungshandbuch

from kohlrahbi.unfoldedahb import UnfoldedAhbTableMetaData
from kohlrahbi.unfoldedahb.unfoldedahbline import UnfoldedAhbLine
from kohlrahbi.unfoldedahb.unfoldedahbtable import UnfoldedAhb


class TestUnfoldedAhbTable:
    """
    All tests regarding the AhbTable class
    """

    def test_from_ahb_table(self):
        pass

    def test_get_section_name(self):
        pass

    def test_is_section_name(self):
        pass

    def test_is_segment_group(self):
        pass

    def test_is_segment_opening_line(self):
        pass

    def test_is_just_segment(self):
        pass

    def test_is_dataelement(self):
        pass

    def test_convert_to_flat_ahb(self) -> None:
        meta_data = UnfoldedAhbTableMetaData(
            pruefidentifikator="55016", beschreibung="Kündigung beim alten Lieferanten", kommunikation_von="LFN an LFA"
        )

        unfolded_ahb_lines = [
            UnfoldedAhbLine(
                index=0,
                segment_name="Ansprechpartner",
                segment_gruppe="SG3",
                segment=None,
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung=None,
                bedingung_ausdruck="Kann",
                bedingung=None,
            ),
            UnfoldedAhbLine(
                index=1,
                segment_name="Ansprechpartner",
                segment_gruppe="SG3",
                segment=None,
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung=None,
                bedingung_ausdruck="Kann",
                bedingung=None,
            ),
            UnfoldedAhbLine(
                index=2,
                segment_name="Ansprechpartner",
                segment_gruppe="SG3",
                segment="CTA",
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung=None,
                bedingung_ausdruck="Muss",
                bedingung=None,
            ),
            UnfoldedAhbLine(
                index=3,
                segment_name="Ansprechpartner",
                segment_gruppe="SG3",
                segment="CTA",
                datenelement="3139",
                code="IC",
                qualifier=None,
                beschreibung="Informationskontakt",
                bedingung_ausdruck="X",
                bedingung=None,
            ),
            UnfoldedAhbLine(
                index=4,
                segment_name="Ansprechpartner",
                segment_gruppe="SG3",
                segment="CTA",
                datenelement="3412",
                code=None,
                qualifier="Name vom Ansprechpartner",
                beschreibung=None,
                bedingung_ausdruck="X",
                bedingung=None,
            ),
        ]

        unfolded_ahb = UnfoldedAhb(meta_data=meta_data, unfolded_ahb_lines=unfolded_ahb_lines)

        expected_flat_ahb: FlatAnwendungshandbuch = FlatAnwendungshandbuch(
            meta=AhbMetaInformation(
                pruefidentifikator="55016",
                description="Kündigung beim alten Lieferanten",
                direction="LFN an LFA",
            ),
            lines=[
                AhbLine(
                    guid=None,
                    section_name="Ansprechpartner",
                    segment_group_key="SG3",
                    segment_code=None,
                    data_element=None,
                    value_pool_entry=None,
                    name=None,
                    ahb_expression="Kann",
                    index=0,
                ),
                AhbLine(
                    guid=None,
                    section_name="Ansprechpartner",
                    segment_group_key="SG3",
                    segment_code=None,
                    data_element=None,
                    value_pool_entry=None,
                    name=None,
                    ahb_expression="Kann",
                    index=1,
                ),
                AhbLine(
                    guid=None,
                    section_name="Ansprechpartner",
                    segment_group_key="SG3",
                    segment_code="CTA",
                    data_element=None,
                    value_pool_entry=None,
                    name=None,
                    ahb_expression="Muss",
                    index=2,
                ),
                AhbLine(
                    guid=None,
                    section_name="Ansprechpartner",
                    segment_group_key="SG3",
                    segment_code="CTA",
                    data_element="3139",
                    value_pool_entry="IC",
                    name="Informationskontakt",
                    ahb_expression="X",
                    index=3,
                ),
                AhbLine(
                    guid=None,
                    section_name="Ansprechpartner",
                    segment_group_key="SG3",
                    segment_code="CTA",
                    data_element="3412",
                    value_pool_entry=None,
                    name="Name vom Ansprechpartner",
                    ahb_expression="X",
                    index=4,
                ),
            ],
        )

        flat_ahb: FlatAnwendungshandbuch = unfolded_ahb.convert_to_flat_ahb()
        assert isinstance(flat_ahb, FlatAnwendungshandbuch)
        assert expected_flat_ahb.meta == flat_ahb.meta

        for expected_ahb_line, ahb_line in zip(expected_flat_ahb.lines, flat_ahb.lines):
            # overwrite the guid with None to match the expected flat ahb
            ahb_line.guid = None
            assert expected_ahb_line == ahb_line

        assert expected_flat_ahb == flat_ahb

    def test_convert_to_dataframe(self):
        pass

    def test_collect_condition(self) -> None:
        meta_data = UnfoldedAhbTableMetaData(
            pruefidentifikator="44014", beschreibung="Anmeldung EOG", kommunikation_von="NB an LF"
        )

        unfolded_ahb_lines = [
            UnfoldedAhbLine(
                index=0,
                segment_name="segment_name",
                segment_gruppe=None,
                segment=None,
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung=None,
                bedingung_ausdruck=None,
                bedingung="[1] Normale Bedingung",
            ),
            UnfoldedAhbLine(
                index=1,
                segment_name="segment_name",
                segment_gruppe=None,
                segment=None,
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung=None,
                bedingung_ausdruck=None,
                bedingung="[2] 2. normale Bedingung\n[3] gefolgt von einer zweiten [4] und dritten",
            ),
            UnfoldedAhbLine(
                index=2,
                segment_name="segment_name",
                segment_gruppe=None,
                segment=None,
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung=None,
                bedingung_ausdruck=None,
                bedingung="[1] Normale Bedingung mit längerem Text",
            ),
            UnfoldedAhbLine(
                index=3,
                segment_name="segment_name",
                segment_gruppe=None,
                segment=None,
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung=None,
                bedingung_ausdruck=None,
                bedingung="[5] Länger Bedingung \n über mehrere\n Zeilen\n",
            ),
            UnfoldedAhbLine(
                index=4,
                segment_name="segment_name",
                segment_gruppe=None,
                segment=None,
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung=None,
                bedingung_ausdruck=None,
                bedingung="[6] Länger Bedingung \n über mehrere\n Zeilen\n[7] gefolgt von noch einer\n über\n Zeilen",
            ),
            UnfoldedAhbLine(
                index=5,
                segment_name="segment_name",
                segment_gruppe=None,
                segment=None,
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung=None,
                bedingung_ausdruck=None,
                bedingung="[8]   Länger Bedi   ngung \n mit  \n zu viel White space\n\n[9] gefolgt \n über\n Zeilen",
            ),
            UnfoldedAhbLine(
                index=6,
                segment_name="segment_name",
                segment_gruppe=None,
                segment=None,
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung=None,
                bedingung_ausdruck=None,
                bedingung="[keine Zahl] mit einem Text",
            ),
            UnfoldedAhbLine(
                index=7,
                segment_name="segment_name",
                segment_gruppe=None,
                segment=None,
                datenelement=None,
                code=None,
                qualifier=None,
                beschreibung="keine Bedingung",
                bedingung_ausdruck=None,
                bedingung="",
            ),
        ]

        unfolded_ahb = UnfoldedAhb(meta_data=meta_data, unfolded_ahb_lines=unfolded_ahb_lines)
        collected_conditions: dict[EdifactFormat, dict[str, str]] = {}
        unfolded_ahb.collect_condition(already_known_conditions=collected_conditions)

        assert len(collected_conditions) == 1
        assert EdifactFormat.UTILMD in collected_conditions
        assert len(collected_conditions[EdifactFormat.UTILMD]) == 9
        assert (
            "1" in collected_conditions[EdifactFormat.UTILMD]
            and collected_conditions[EdifactFormat.UTILMD]["1"] == "Normale Bedingung mit längerem Text"
        )
        assert (
            "2" in collected_conditions[EdifactFormat.UTILMD]
            and collected_conditions[EdifactFormat.UTILMD]["2"] == "2. normale Bedingung"
        )
        assert (
            "3" in collected_conditions[EdifactFormat.UTILMD]
            and collected_conditions[EdifactFormat.UTILMD]["3"] == "gefolgt von einer zweiten"
        )
        assert (
            "4" in collected_conditions[EdifactFormat.UTILMD]
            and collected_conditions[EdifactFormat.UTILMD]["4"] == "und dritten"
        )
        assert (
            "5" in collected_conditions[EdifactFormat.UTILMD]
            and collected_conditions[EdifactFormat.UTILMD]["5"] == "Länger Bedingung über mehrere Zeilen"
        )
        assert (
            "6" in collected_conditions[EdifactFormat.UTILMD]
            and collected_conditions[EdifactFormat.UTILMD]["6"] == "Länger Bedingung über mehrere Zeilen"
        )
        assert (
            "7" in collected_conditions[EdifactFormat.UTILMD]
            and collected_conditions[EdifactFormat.UTILMD]["7"] == "gefolgt von noch einer über Zeilen"
        )
        assert (
            "8" in collected_conditions[EdifactFormat.UTILMD]
            and collected_conditions[EdifactFormat.UTILMD]["8"] == "Länger Bedi ngung mit zu viel White space"
        )
        assert (
            "9" in collected_conditions[EdifactFormat.UTILMD]
            and collected_conditions[EdifactFormat.UTILMD]["9"] == "gefolgt über Zeilen"
        )
        assert "keine Zahl" not in collected_conditions[EdifactFormat.UTILMD]
        assert "Normale Bedingung" not in collected_conditions[EdifactFormat.UTILMD].values()
