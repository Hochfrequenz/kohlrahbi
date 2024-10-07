"""
This module provides the QualityMapTable class
"""

from pathlib import Path

import pandas as pd
from docx.table import Table
from pydantic import BaseModel, ConfigDict

from kohlrahbi.ahbtable.ahbsubtable import AhbSubTable
from kohlrahbi.logger import logger


class QualityMapTable(BaseModel):
    """
    This class contains the quality map table.

    Die SG für die Datenübermittlung haben in den Segmenten DE1153 SG6 RFF, DE1229 SG8 SEQ und DE3035 SG12 NAD
    verschiedene Codes, die die Qualität der enthaltenen Daten festlegen.
    Die Qualitätsstufen sind:
        •   Bestellte Daten: Konfiguration, die der Absender beim Empfänger bestellt.
        •   Gültige Daten: Verbindliche Stammdaten, die vom Verantwortlichen bereitgestellt und
                           vom Berechtigten übernommen werden müssen.
        •   Informative Daten: Datenstand des Absenders zum Zeitpunkt der Nachricht, ohne Gültigkeitszeitraum,
                               nur zur Information im entsprechenden Use-Case.
        •   Erwartete Daten: Erwartung des Berechtigten, nur für Abrechnungsdaten, Stammdatenänderungen und
                             Datenclearing relevant.
        •   Im System vorhandene Daten: Datenstand des Berechtigten, ausschließlich für das Datenclearing.
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

            is_header_row = sanitized_cells[0].text.strip() == "Qualität\n\nSegmentgruppe"
            if is_header_row:
                continue
            quality_map_rows.append([cell.text for cell in sanitized_cells])

        headers = [
            "Qualität \\ Segmentgruppe",
            "Bestellte Daten",
            "Gültige Daten",
            "Informative Daten",
            "Erwartete Daten",
            "Im System vorhandene Daten",
        ]

        df = pd.DataFrame(quality_map_rows, columns=headers)

        return cls(table=df)

    def save_to_csv(self, output_path: Path) -> None:
        """
        Save the quality map table to a csv file.
        """
        self.table.to_csv(output_path, index=False, encoding="utf-8")
        logger.info("💾 Saved quality map table to '%s'", output_path)

    def save_to_xlsx(self, output_path: Path) -> None:
        """
        Save the quality map table to an xlsx file.
        """
        self.table.to_excel(output_path, index=False)
        logger.info("💾 Saved quality map table to '%s'", output_path)
