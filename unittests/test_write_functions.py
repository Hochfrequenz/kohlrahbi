from typing import List

import docx
import pandas as pd
import pytest

from write_functions import parse_paragraph_in_middle_column_to_dataframe


class TestWriteFunctions:

    # this left indent and tabstop positions are equal to
    # the left indent and tabstop positions of the indicator paragraph
    left_indent_position_of_indicator_paragraph = 36830
    tabstop_positions_of_indicator_paragraph = [436245, 1962785, 2578735, 3192780]

    @pytest.mark.parametrize(
        "text_content, left_indent_position, cell_tabstop_positions, expected_df_row",
        [
            pytest.param(
                "",
                None,
                None,
                {
                    "Segment Gruppe": "",
                    "Segment": "",
                    "Datenelement": "",
                    "Codes und Qualifier": "",
                    "Beschreibung": "",
                    "77777": "",
                    "88888": "",
                    "99999": "",
                    "Bedingung": "",
                },
                id="Segmentname Nachrichten-Kopfsegment",
            ),
            pytest.param(
                "\tMuss\tMuss\tMuss",
                None,
                tabstop_positions_of_indicator_paragraph,
                {
                    "Segment Gruppe": "",
                    "Segment": "",
                    "Datenelement": "",
                    "Codes und Qualifier": "",
                    "Beschreibung": "",
                    "77777": "Muss",
                    "88888": "Muss",
                    "99999": "Muss",
                    "Bedingung": "",
                },
                id="First UNH Segment",
            ),
            pytest.param(
                "Nachrichten-Referenznummer\tX\tX\tX",
                left_indent_position_of_indicator_paragraph,
                tabstop_positions_of_indicator_paragraph[1:],
                {
                    "Segment Gruppe": "",
                    "Segment": "",
                    "Datenelement": "",
                    "Codes und Qualifier": "Nachrichten-Referenznummer",
                    "Beschreibung": "",
                    "77777": "X",
                    "88888": "X",
                    "99999": "X",
                    "Bedingung": "",
                },
                id="Qualifier",
            ),
            pytest.param(
                "UTILM\tNetzanschluss-\tX\tX\tX",
                left_indent_position_of_indicator_paragraph,
                tabstop_positions_of_indicator_paragraph,
                {
                    "Segment Gruppe": "",
                    "Segment": "",
                    "Datenelement": "",
                    "Codes und Qualifier": "UTILM",
                    "Beschreibung": "Netzanschluss-",
                    "77777": "X",
                    "88888": "X",
                    "99999": "X",
                    "Bedingung": "",
                },
                id="First Dataelement",
            ),
            pytest.param(
                "D\tStammdaten",
                left_indent_position_of_indicator_paragraph,
                tabstop_positions_of_indicator_paragraph[0:1],
                {
                    "Segment Gruppe": "",
                    "Segment": "",
                    "Datenelement": "",
                    "Codes und Qualifier": "D",
                    "Beschreibung": "Stammdaten",
                    "77777": "",
                    "88888": "",
                    "99999": "",
                    "Bedingung": "",
                },
                id="Dataelement without conditions",
            ),
            pytest.param(
                "zugrundeliegenden",
                tabstop_positions_of_indicator_paragraph[0],
                None,
                {
                    "Segment Gruppe": "",
                    "Segment": "",
                    "Datenelement": "",
                    "Codes und Qualifier": "",
                    "Beschreibung": "zugrundeliegenden",
                    "77777": "",
                    "88888": "",
                    "99999": "",
                    "Bedingung": "",
                },
                id="only Beschreibung",
            ),
            pytest.param(
                "\tMuss [16] U\n",
                None,
                tabstop_positions_of_indicator_paragraph[-1:],
                {
                    "Segment Gruppe": "",
                    "Segment": "",
                    "Datenelement": "",
                    "Codes und Qualifier": "",
                    "Beschreibung": "",
                    "77777": "",
                    "88888": "",
                    "99999": "Muss [16] U\n",
                    "Bedingung": "",
                },
                id="Just one entry for one Prüfidentifikator",
            ),
        ],
    )
    def test_parse_paragraph_in_middle_column(
        self, text_content, left_indent_position, cell_tabstop_positions, expected_df_row
    ):

        # create table test cell, it contains per default an empty paragraph
        test_document = docx.Document()
        test_table = test_document.add_table(rows=1, cols=1)
        test_cell = test_table.add_row().cells[0]

        # insert text
        test_cell.text = text_content
        test_paragraph = test_cell.paragraphs[0]

        # set left indent positon
        test_paragraph.paragraph_format.left_indent = left_indent_position

        tab_stops = test_paragraph.paragraph_format.tab_stops
        # Length: https://python-docx.readthedocs.io/en/latest/api/shared.html#docx.shared.Length

        if cell_tabstop_positions is not None:
            for tabstop_position in cell_tabstop_positions:
                tab_stops.add_tab_stop(tabstop_position)

        # Initial two dataframes ...
        df = pd.DataFrame(columns=expected_df_row.keys(), dtype="str")
        expected_df = pd.DataFrame(columns=expected_df_row.keys(), dtype="str")
        row_index = 0
        # ... with a row full of emtpy strings
        initial_dataframe_row = (len(df.columns)) * [""]
        df.loc[row_index] = initial_dataframe_row
        expected_df.loc[row_index] = initial_dataframe_row

        parse_paragraph_in_middle_column_to_dataframe(
            paragraph=test_paragraph,
            dataframe=df,
            row_index=row_index,
            left_indent_position=self.left_indent_position_of_indicator_paragraph,
            tabstop_positions=self.tabstop_positions_of_indicator_paragraph,
        )

        expected_df.loc[row_index] = expected_df_row

        assert expected_df.equals(df)
