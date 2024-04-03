import pandas as pd
from docx.table import Table as DocxTable  # type: ignore[import-untyped]
from maus.edifact import EdifactFormat
from pydantic import BaseModel, ConfigDict


class AhbConditions(BaseModel):
    edifact_format: EdifactFormat = None
    conditions: pd.DataFrame
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_docx_table(cls, docx_tables: list[DocxTable]) -> "AhbConditions":
        """
        Create an AhbPackageTable object from a docx table.

        """
        table_data = []
        for table in docx_tables:
            for row in table.rows:
                if row.cells[-1].text and row.cells[0].text != "EDIFACT Struktur":
                    row_data = row.cells[-1].text
                    table_data.append(row_data)

        headers = ["Bedingung"]
        df = pd.DataFrame(table_data, columns=headers)
        return cls(table=df)
