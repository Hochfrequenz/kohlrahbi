import maus
import pandas as pd
from maus.models.anwendungshandbuch import AhbLine, AhbMetaInformation, FlatAnwendungshandbuch

from kohlrahbi.dump.flatahb import convert_ahb_table_to_flatahb


def test_convert_ahb_table_to_flatahb():

    ahb_table: pd.DataFrame = pd.DataFrame(
        {
            "Segment Gruppe": ["Ansprechpartner", "SG3", "SG3", "SG3", "SG3"],
            "Segment": ["", "", "CTA", "CTA", "CTA"],
            "Datenelement": ["", "", "", "3139", "3412"],
            "Codes und Qualifier": ["", "", "", "IC", "Name vom Ansprechpartner"],
            "Beschreibung": [
                "",
                "",
                "",
                "Informationskontakt",
                "",
            ],
            "11016": ["", "Kann", "Muss", "X", "X"],
            "11017": ["", "Kann", "Muss", "X", "X"],
            "11018": ["", "Kann", "Muss", "X", "X"],
            "Bedingung": ["", "", "", "", ""],
        }
    )

    expected_flat_ahb: FlatAnwendungshandbuch = FlatAnwendungshandbuch(
        meta=AhbMetaInformation(pruefidentifikator="11016"),
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
                ahb_expression="Muss",
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

    flat_ahb: FlatAnwendungshandbuch = convert_ahb_table_to_flatahb(ahb_table=ahb_table, pruefi="11016")
    assert isinstance(flat_ahb, FlatAnwendungshandbuch)
    assert expected_flat_ahb.meta == flat_ahb.meta

    for expected_ahb_line, ahb_line in zip(expected_flat_ahb.lines, flat_ahb.lines):
        # overwrite the guid with None to match the expected flat ahb
        ahb_line.guid = None
        assert expected_ahb_line == ahb_line

    assert expected_flat_ahb == flat_ahb
