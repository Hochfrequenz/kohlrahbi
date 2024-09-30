"""
This module provides the QualityMapTable class
"""

import re
from collections import OrderedDict
from pathlib import Path
from typing import Annotated

import pandas as pd
from docx.table import Table
from pydantic import BaseModel, ConfigDict, Field, PlainValidator

from kohlrahbi.ahbtable.ahbsubtable import AhbSubTable
from kohlrahbi.logger import logger

StrippedStr = Annotated[str, PlainValidator(str.strip)]
Description = Annotated[str, PlainValidator(str.strip), PlainValidator(lambda value: re.sub(r"\n+", " ", value))]
HEADERS = OrderedDict(
    [
        ("segment_group", "Qualität \\ Segmentgruppe"),
        ("bestellte_daten", "Bestellte Daten"),
        ("gueltige_daten", "Gültige Daten"),
        ("informative_daten", "Informative Daten"),
        ("erwartete_daten", "Erwartete Daten"),
        ("im_system_vorhandene_daten", "Im System vorhandene Daten"),
    ]
)


class Cell(BaseModel):
    """Here some docstring

    Attributes:
        qualifier: Qualifier for the Edifact message e.g "Z50"
        description: Description
    """

    qualifier: StrippedStr
    description: Description


class SegmentGroup(BaseModel):
    path_to_data_element: StrippedStr
    description: Description


class Row(BaseModel):
    segment_group: SegmentGroup
    bestellte_daten: list[Cell] = Field(default_factory=list)
    gueltige_daten: list[Cell] = Field(default_factory=list)
    informative_daten: list[Cell] = Field(default_factory=list)
    erwartete_daten: list[Cell] = Field(default_factory=list)
    im_system_vorhandene_daten: list[Cell] = Field(default_factory=list)


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

    rows: list[Row] = Field(default_factory=list)

    @classmethod
    def from_raw_table(cls, raw_table: list[list[str]]) -> "QualityMapTable":
        """
        Create a QualityMapTable object from a raw table.
        """
        rows = []
        for row in raw_table:
            path_to_data_element, description = row[0].strip().split("\n", 1)
            segment_group = SegmentGroup(path_to_data_element=path_to_data_element, description=description)
            row_dict = {
                "segment_group": segment_group,
                **{header: [] for header in HEADERS if header != "segment_group"},
            }

            for column_name, column in zip(
                (header for header in HEADERS if header != "segment_group"),
                row[1:],
            ):
                column = column.strip()
                if column == "--":
                    continue
                raw_cells = column.strip().split("\n\n")
                for raw_cell in raw_cells:
                    qualifier, description = raw_cell.split("\n", 1)
                    description = description.strip('"„“')
                    cell = Cell(qualifier=qualifier, description=description)
                    row_dict[column_name].append(cell)

            rows.append(Row.model_validate(row_dict))
        return cls(rows=rows)

    def to_raw_table(self) -> list[list[str]]:
        """
        Create a raw table from the quality map table.
        """
        raw_table = []
        for row in self.rows:
            raw_row = []
            for header in HEADERS:
                if header == "segment_group":
                    raw_row.append(f"{row.segment_group.path_to_data_element}\n{row.segment_group.description}")
                    continue
                raw_cells = []
                for cell in getattr(row, header):
                    raw_cells.append(f"{cell.qualifier}\n„{cell.description}“")

                raw_row.append("\n\n".join(raw_cells) if len(raw_cells) > 0 else "--")
            raw_table.append(raw_row)
        return raw_table

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

        return cls.from_raw_table(quality_map_rows)

    def save_to_csv(self, output_path: Path) -> None:
        """
        Save the quality map table to a csv file.
        """
        df = pd.DataFrame(self.to_raw_table(), columns=list(HEADERS.values()))
        df.to_csv(output_path, index=False, encoding="utf-8")
        logger.info("💾 Saved quality map table to '%s'", output_path)

    def save_to_xlsx(self, output_path: Path) -> None:
        """
        Save the quality map table to an xlsx file.
        """
        df = pd.DataFrame(self.to_raw_table(), columns=list(HEADERS.values()))
        df.to_excel(output_path, index=False)
        logger.info("💾 Saved quality map table to '%s'", output_path)
