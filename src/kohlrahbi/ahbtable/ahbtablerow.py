"""
This module contains the class AhbTableRow
"""

from typing import Optional

import pandas as pd
from docx.table import _Cell
from pydantic import BaseModel, ConfigDict

from kohlrahbi.docxtablecells import BedingungCell, BodyCell, EdifactStrukturCell
from kohlrahbi.enums import RowType
from kohlrahbi.seed import Seed


# pylint:disable=too-few-public-methods
class AhbTableRow(BaseModel):
    """
    A AhbTableRow is a single row from an AHB table.
    It contains a seed and the three cells (columns).
    """

    seed: Seed
    edifact_struktur_cell: _Cell
    middle_cell: _Cell
    bedingung_cell: _Cell

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def parse(
        self,
        row_type: RowType,
    ) -> Optional[pd.DataFrame]:
        """
        Writes the current row of the current table into the DataFrame depending on the type of the row.
        If the row is a header row, it will be skipped and None will be returned.
        """

        if row_type is RowType.HEADER:
            # we skip the header rows because we scraped it already and there are no new information
            return None

        ahb_row_dataframe = pd.DataFrame(
            # pylint: disable=no-member
            columns=self.seed.column_headers,
            dtype="str",
        )
        # pylint: disable=unsubscriptable-object, no-member
        empty_row: pd.Series = pd.Series(  # type:ignore[type-arg]
            len(ahb_row_dataframe.columns) * [""], index=self.seed.column_headers
        )

        ahb_row_dataframe = pd.concat([ahb_row_dataframe, empty_row.to_frame().T], ignore_index=True)

        # EDIFACT STRUKTUR
        esc: EdifactStrukturCell = EdifactStrukturCell(
            # pylint: disable=no-member
            table_cell=self.edifact_struktur_cell,
            edifact_struktur_cell_left_indent_position=self.seed.edifact_struktur_left_indent_position,
        )
        ahb_row_dataframe = esc.parse(ahb_row_dataframe=ahb_row_dataframe)

        # BODY
        boc: BodyCell = BodyCell(
            # pylint: disable=no-member
            table_cell=self.middle_cell,
            left_indent_position=self.seed.middle_cell_left_indent_position,
            indicator_tabstop_positions=self.seed.tabstop_positions,
        )
        ahb_row_dataframe = boc.parse(ahb_row_dataframe=ahb_row_dataframe)

        # BEDINGUNG
        bec: BedingungCell = BedingungCell(table_cell=self.bedingung_cell)
        ahb_row_dataframe = bec.parse(ahb_row_dataframe)

        return ahb_row_dataframe
