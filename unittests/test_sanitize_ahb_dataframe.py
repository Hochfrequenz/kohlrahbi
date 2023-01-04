import pandas as pd
import pytest

from kohlrahbi.helper.read_functions import sanitize_ahb_table_dataframe


# Zeile 648 im Dataframe!
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
def test_sanitize_ahb_dataframe(ahb_table_dataframe, expected_ahb_table_dataframe):
    """ """
    sanitized_ahb_table_dataframe: pd.DataFrame = sanitize_ahb_table_dataframe(ahb_table_dataframe=ahb_table_dataframe)

    assert len(sanitized_ahb_table_dataframe) == len(expected_ahb_table_dataframe)
    assert sanitized_ahb_table_dataframe.equals(expected_ahb_table_dataframe)
