from typing import List

import docx
import pandas as pd
import pytest

from write_functions import parse_paragraph_in_middle_column_to_dataframe


class TestWriteFunctions:
    @pytest.mark.parametrize(
        "text_content, left_indent_position, cell_tabstop_positions, expected_df_row",
        [
            pytest.param(
                "\tMuss\tMuss\tMuss",
                None,
                [436245, 1962785, 2578735, 3192780],
                ["", "", "", "", "", "Muss", "Muss", "Muss", ""],
                id="First UNH Segment",
            ),
            pytest.param(
                "Nachrichten-Referenznummer\tX\tX\tX",
                36830,
                [1962785, 2578735, 3192780],
                ["", "", "", "Nachrichten-Referenznummer", "", "X", "X", "X", ""],
                id="Qualifier",
            ),
            pytest.param(
                "UTILM\tNetzanschluss-\tX\tX\tX",
                36830,
                [436245, 1962785, 2578735, 3192780],
                ["", "", "", "UTILM", "Netzanschluss-", "X", "X", "X", ""],
                id="First Dataelement",
            ),
            pytest.param(
                "D\tStammdaten",
                36830,
                [436245],
                ["", "", "", "D", "Stammdaten", "", "", "", ""],
                id="Dataelement without conditions",
            ),
            pytest.param(
                "zugrundeliegenden",
                436245,
                None,
                ["", "", "", "", "zugrundeliegenden", "", "", "", ""],
                id="only Beschreibung",
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

        # this left indent position is equal to the left indent position of the indicator paragraph
        middle_cell_left_indent_position = 36830
        tabstop_positions = [436245, 1962785, 2578735, 3192780]

        # set left indent positon
        test_paragraph.paragraph_format.left_indent = left_indent_position

        tab_stops = test_paragraph.paragraph_format.tab_stops
        # Length: https://python-docx.readthedocs.io/en/latest/api/shared.html#docx.shared.Length

        if cell_tabstop_positions is not None:
            for tabstop_position in cell_tabstop_positions:
                tab_stops.add_tab_stop(tabstop_position)

        # Create column names
        base_columns: List = [
            "Segment Gruppe",
            "Segment",
            "Datenelement",
            "Codes und Qualifier",
            "Beschreibung",
        ]
        columns = base_columns + ["77777", "88888", "99999"]
        columns.append("Bedingung")

        # Initial two dataframes
        df = pd.DataFrame(columns=columns, dtype="str")
        expected_df = pd.DataFrame(columns=columns, dtype="str")
        initial_dataframe_row = (len(df.columns)) * [""]

        row_index = 0
        df.loc[row_index] = initial_dataframe_row
        expected_df.loc[row_index] = initial_dataframe_row

        parse_paragraph_in_middle_column_to_dataframe(
            paragraph=test_paragraph,
            dataframe=df,
            row_index=row_index,
            left_indent_position=middle_cell_left_indent_position,
            tabstop_positions=tabstop_positions,
        )

        expected_df.loc[row_index] = expected_df_row

        assert expected_df.equals(df)
