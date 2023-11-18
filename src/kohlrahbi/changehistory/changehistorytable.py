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

            if sanitized_cells[0].text == "Änd-ID" or sanitized_cells[0].text == "":
                continue
            else:
                change_history_rows.append([cell.text for cell in sanitized_cells])

        headers = ["Änd-ID", "Ort", "Änderungen Bisher", "Änderungen Neu", "Grund der Anpassung", "Status"]

        df = pd.DataFrame(change_history_rows, columns=headers)

        return cls(table=df)
