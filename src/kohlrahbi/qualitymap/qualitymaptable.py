"""
This module provides the QualityMapTable class
"""

import pandas as pd
from docx.table import Table
from pydantic import BaseModel, ConfigDict

from kohlrahbi.ahbtable.ahbsubtable import AhbSubTable


class QualityMapTable(BaseModel):
    """
    This class contains the quality map table.
    """

    table: pd.DataFrame

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_docx_quality_map_table(cls, docx_table: Table) -> "QualityMapTable":
        """
        Create a QualityMapTable object from a quality map table.
        """

        quality_map_rows: list[list[str]] = []

        for row in docx_table.rows:
            sanitized_cells = list(AhbSubTable.iter_visible_cells(row=row))

            is_header_row = sanitized_cells[0].text == "Änd-ID" or sanitized_cells[2].text == "Bisher"
            if is_header_row:
                continue
            quality_map_rows.append([cell.text for cell in sanitized_cells])

        headers = ["Änd-ID", "Ort", "Änderungen Bisher", "Änderungen Neu", "Grund der Anpassung", "Status"]

        df = pd.DataFrame(quality_map_rows, columns=headers)

        return cls(table=df)
