import attrs
import pandas as pd
from docx.table import _Cell  # type:ignore[import]
from typing import Optional
from kohlrahbi.helper.seed import Seed
from kohlrahbi.helper.row_type_checker import RowType
from kohlrahbi.cells import EdifactStrukturCell, BodyCell, BedingungCell


@attrs.define(auto_attribs=True, kw_only=True)
class AhbTableRow:
    seed: Seed
    edifact_struktur_cell: _Cell
    middle_cell: _Cell
    bedingung_cell: _Cell

    def parse(
        self,
        row_type: RowType,
        is_appending: bool = False,
    ) -> Optional[pd.DataFrame]:
        """Writes the current row of the current table into the DataFrame depending on the type of the row

        Args:
            seed (Seed):
            row_type (RowType): Type of the current row
            ahb_table (Table): Current table
            ahb_table_row (int): Row of the current ahb table
            index_for_middle_column (int): Index of the actual middle column
            is_appending (bool):
        """

        if row_type is RowType.HEADER:
            # we skip the header rows because there we did it already and there are no new information
            return

        ahb_row_dataframe = pd.DataFrame(
            columns=self.seed.column_headers,
            dtype="str",
        )

        ahb_row_dataframe.loc[0] = (len(ahb_row_dataframe.columns)) * [""]

        # edifact_struktur_cell = self.table.row_cells(self.table_row)[0]
        # middle_cell = self.table.row_cells(self.table_row)[index_for_middle_column]
        # bedingung_cell = self.table.row_cells(self.table_row)[-1]

        if not is_appending:
            self.seed.soul.loc[self.seed.soul.index.max() + 1, :] = ""

        # EDIFACT STRUKTUR
        esc = EdifactStrukturCell(
            table_cell=self.edifact_struktur_cell,
            edifact_struktur_cell_left_indent_position=self.seed.edifact_struktur_left_indent_position,
        )
        ahb_row_dataframe = esc.parse(ahb_row_dataframe=ahb_row_dataframe)

        # BODY
        boc = BodyCell(
            table_cell=self.middle_cell,
            left_indent_position=self.seed.middle_cell_left_indent_position,
            indicator_tabstop_positions=self.seed.tabstop_positions,
        )
        ahb_row_dataframe = boc.parse(ahb_row_dataframe=ahb_row_dataframe)

        # BEDINGUNG
        bec = BedingungCell(table_cell=self.bedingung_cell)
        ahb_row_dataframe = bec.parse(ahb_row_dataframe)

        return ahb_row_dataframe
