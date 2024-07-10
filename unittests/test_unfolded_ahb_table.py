import pytest
from maus.edifact import EdifactFormat
from maus.models.anwendungshandbuch import AhbLine, AhbMetaInformation, FlatAnwendungshandbuch

from kohlrahbi.unfoldedahb import UnfoldedAhbTableMetaData
from kohlrahbi.unfoldedahb.unfoldedahbline import UnfoldedAhbLine
from kohlrahbi.unfoldedahb.unfoldedahbtable import UnfoldedAhb, _remove_irrelevant_lines


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
            UnfoldedAhbLine(
                index=5,
                segment_name="Marktlokation",
                segment_gruppe="SG5",
                segment="LOC",
                datenelement="3225",
                code=None,
                qualifier="ID der Marktlokation",
                beschreibung=None,
                bedingung_ausdruck="X[950]",
                bedingung="[950] Format:\n Marktlokations-ID",
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
                    section_name=None,
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
                    section_name=None,
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
                AhbLine(
                    guid=None,
                    section_name="Marktlokation",
                    conditions="[950] Format:\n Marktlokations-ID",
                    segment_group_key="SG5",
                    segment_code="LOC",
                    data_element="3225",
                    value_pool_entry=None,
                    name="ID der Marktlokation",
                    ahb_expression="X[950]",
                    index=5,
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

    @pytest.mark.parametrize(
        "input_lines, expected_output",
        [
            pytest.param(
                [
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
                [
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
                id="Generic Case",
            ),
            pytest.param(
                [
                    AhbLine(
                        guid=None,
                        section_name=None,
                        segment_group_key="SG3",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        index=3,
                    ),
                ],
                [],
                id="Next Line None and only SH_header",
            ),
            pytest.param(
                [
                    AhbLine(
                        guid=None,
                        section_name=None,
                        segment_group_key="SG3",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        index=0,
                    ),
                    AhbLine(
                        guid=None,
                        section_name=None,
                        segment_group_key="SG3",
                        segment_code=None,
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        index=1,
                    ),
                ],
                [],
                id="Next Line empty and only SH_header",
            ),
            pytest.param(
                [
                    AhbLine(
                        guid=None,
                        section_name="Ansprechpartner",
                        segment_group_key="SG3",
                        segment_code="CTA",
                        data_element=None,
                        value_pool_entry=None,
                        name=None,
                        ahb_expression=None,
                        index=0,
                    ),
                ],
                [],
                id="Empty Line",
            ),
        ],
    )
    def test_remove_irrelevant_lines(self, input_lines, expected_output):
        assert _remove_irrelevant_lines(input_lines) == expected_output
