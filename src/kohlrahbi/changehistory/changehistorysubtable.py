"""
This module provides the ChangeHistorySubTable class
"""
import attrs
import pandas as pd
from docx.table import Table  # type:ignore[import]

from kohlrahbi.ahb.ahbsubtable import AhbSubTable


@attrs.define(auto_attribs=True, kw_only=True)
class ChangeHistorySubTable:
    """
    This class  contains the change history table.
    """

    table: pd.DataFrame

    @classmethod
    def from_docx_change_history_table(cls, docx_table: Table) -> "ChangeHistorySubTable":
        """
        Create a ChangeHistorySubTable object from a change history table.
        """

        change_history_rows: list[list[str]] = []

        for row in docx_table.rows:
            sanitized_cells = list(AhbSubTable._iter_visible_cells(row=row))

            if sanitized_cells[0].text == "Änd-ID" or sanitized_cells[0].text == "":
                continue
            else:
                change_history_rows.append([cell.text for cell in sanitized_cells])

        headers = ["Änd-ID", "Ort", "Änderungen Bisher", "Änderungen Neu", "Grund der Anpassung", "Status"]

        df = pd.DataFrame(change_history_rows, columns=headers)

        return cls(table=df)

    @staticmethod
    def sanitize_header(first_list: list[str], second_list: list[str]) -> list[str]:
        """
        The first row of the table looks like this:

        Änd-ID; Änd-IDM; Ort; Ort; Änderungen; Änderungen; Grund der Anpassung; Status

        which is okay, but it appears again and again in the table.
        This method removes these all duplicate rows.
        """

        result: list[str] = []

        for first_element, second_element in zip(first_list, second_list):
            first_element_stripped = first_element.strip()
            second_element_stripped = second_element.strip()
            if first_element_stripped == second_element_stripped:
                result.append(first_element_stripped)
            else:
                result.append(first_element_stripped + " " + second_element_stripped)

        return result

    def sanitize_change_history_table(self):
        """
        The first row of the table looks like this:

        Änd-ID; Änd-IDM; Ort; Ort; Änderungen; Änderungen; Grund der Anpassung; Status

        which is okay, but it appears again and again in the table.
        This method removes these all duplicate rows.
        """

        # We need two combine the first two rows to get the header
        # The first row contains:
        # ['Änd-ID', 'Änd-ID', 'Ort', 'Ort', '\tÄnderungen', '\tÄnderungen', 'Grund der Anpassung', 'Status']
        # The second row contains:
        # ['', '', '', '', 'Bisher', 'Neu', '', '']
        # first_header_row = self.table.iloc[0].to_list()
        # second_header_row = self.table.iloc[1].to_list()

        header = ["Änd-ID", "Ort", "Änderungen Bisher", "Änderungen Neu", "Grund der Anpassung", "Status"]

        # header = ChangeHistorySubTable.sanitize_header(first_header_row, second_header_row)

        # Set header of the dataframe
        self.table.columns = header

        # Remove all rows that start with "Änd-ID"
        self.table = self.table[self.table.iloc[:, 0] != "Änd-ID"]

        # Reset index
        self.table = self.table.reset_index(drop=True)
        print("foo")
