"""
This module provides the ChangeHistoryTable class
"""

import pandas as pd
from docx.table import Table
from pydantic import BaseModel, ConfigDict

from kohlrahbi.ahbtable.ahbsubtable import AhbSubTable


class ChangeHistoryTable(BaseModel):
    """
    This class  contains the change history table.
    """

    table: pd.DataFrame

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_docx_change_history_table(cls, docx_table: Table) -> "ChangeHistoryTable":
        """
        Create a ChangeHistorySubTable object from a change history table.
        """

        change_history_rows: list[list[str]] = []

        for row in docx_table.rows:
            sanitized_cells = list(AhbSubTable.iter_visible_cells(row=row))

            is_header_row = sanitized_cells[0].text == "Änd-ID" or sanitized_cells[2].text == "Bisher"
            if is_header_row:
                continue
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

        def is_empty(val: str) -> bool:
            """
            Checks if the given value is considered empty for our case.
            """
            return pd.isna(val) or val == ""

        # Define a function to check if a value is considered empty for our case
        def is_the_first_column_empty(row: pd.Series) -> bool:  # type:ignore[type-arg]
            """
            Checks if the first column of the given row is empty.
            This is our indicator if the current row is a continuation of the upper row.
            """
            return is_empty(row.iloc[0])

        # Iterate over the DataFrame rows in reverse (to avoid skipping rows after removing them)
        for i in reversed(range(1, len(self.table))):
            # Check if the first and second columns of the current row are empty
            if is_the_first_column_empty(self.table.iloc[i]):
                # Merge with the upper row by concatenating the non-empty values
                for col in range(len(self.table.columns)):
                    cell_entry = self.table.iloc[i, col]
                    if isinstance(cell_entry, str) and not is_empty(cell_entry):
                        self.table.iloc[i - 1, col] = (
                            str(self.table.iloc[i - 1, col]) + " " + str(self.table.iloc[i, col]).strip()
                        )
                # Drop the current row since it has been merged
                self.table.drop(i, inplace=True)

        # Reset index after dropping rows
        self.table.reset_index(drop=True, inplace=True)
