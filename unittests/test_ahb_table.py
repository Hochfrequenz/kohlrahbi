import attrs
import pandas as pd
import pytest  # type:ignore[import]

from kohlrahbi.ahb.ahbtable import AhbTable


@attrs.define(auto_attribs=True, kw_only=True)
class TestAhbTable:
    """
    All tests regarding the AhbTable class
    """

    def test_append_ahb_sub_table(self):
        """
        Test appending of an AHB subtable
        """

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
        """ """

        ahb_table = AhbTable(table=ahb_table_dataframe)

        ahb_table.sanitize()

        assert len(ahb_table.table) == len(expected_ahb_table_dataframe)
        assert ahb_table.table.equals(expected_ahb_table_dataframe)
