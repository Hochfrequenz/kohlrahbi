"""
This module provides the ChangeHistoryTable class
"""
import attrs
import pandas as pd
from docx.table import Table  # type:ignore[import]

from kohlrahbi.ahb.ahbsubtable import AhbSubTable


@attrs.define(auto_attribs=True, kw_only=True)
class ChangeHistoryTable:
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

            is_header_row = sanitized_cells[0].text == "Änd-ID" or sanitized_cells[2].text == "Bisher"
            if is_header_row:
                continue
            else:
                change_history_rows.append([cell.text for cell in sanitized_cells])

        headers = ["Änd-ID", "Ort", "Änderungen Bisher", "Änderungen Neu", "Grund der Anpassung", "Status"]

        df = pd.DataFrame(change_history_rows, columns=headers)

        return cls(table=df)

    def sanitize_table(self) -> None:
        """
        Sanitizes the change history table.
        Thanks to the page breaks in the docx file there are rows which are just a small part of the upper row.
        This function merges these rows.
        """

        # Create a copy of the DataFrame to avoid modifying the original one
        df = self.table.copy()

        def is_empty(val: str) -> bool:
            return pd.isna(val) or val == ""

        # Define a function to check if a value is considered empty for our case
        def are_the_first_two_columns_empty(row: pd.Series) -> bool:
            """
            Checks if the first and second columns of the given row are empty.
            Row is a row from a pandas DataFrame.
            """
            return is_empty(row[0]) and is_empty(row[1])

        # Iterate over the DataFrame rows in reverse (to avoid skipping rows after removing them)
        for i in reversed(range(1, len(df))):
            # Check if the first and second columns of the current row are empty
            if are_the_first_two_columns_empty(df.iloc[i]):
                # Merge with the upper row by concatenating the non-empty values
                for col in range(len(df.columns)):
                    if not is_empty(df.iloc[i, col]):
                        df.iloc[i - 1, col] = str(df.iloc[i - 1, col]) + " " + str(df.iloc[i, col]).strip()
                # Drop the current row since it has been merged
                df.drop(i, inplace=True)

        # Reset index after dropping rows
        df.reset_index(drop=True, inplace=True)

        return df
