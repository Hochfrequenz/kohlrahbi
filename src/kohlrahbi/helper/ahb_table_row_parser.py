"""
Collection of functions to write the extracted infos from the AHB tables into a DataFrame.
"""
import pandas as pd
from docx.table import Table  # type:ignore[import]
from typing import Optional
from kohlrahbi.helper.row_type_checker import RowType
from kohlrahbi.helper.seed import Seed
from kohlrahbi.cells import EdifactStrukturCell, BedingungCell, BodyCell


def parse_ahb_table_row(
    seed: Seed,
    row_type: RowType,
    ahb_table: Table,
    ahb_table_row: int,
    index_for_middle_column: int,
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
        columns=seed.column_headers,
        dtype="str",
    )

    ahb_row_dataframe.loc[0] = (len(ahb_row_dataframe.columns)) * [""]

    edifact_struktur_cell = ahb_table.row_cells(ahb_table_row)[0]
    middle_cell = ahb_table.row_cells(ahb_table_row)[index_for_middle_column]
    bedingung_cell = ahb_table.row_cells(ahb_table_row)[-1]

    if not is_appending:
        seed.soul.loc[seed.soul.index.max() + 1, :] = ""

    # EDIFACT STRUKTUR
    esc = EdifactStrukturCell(
        table_cell=edifact_struktur_cell,
        edifact_struktur_cell_left_indent_position=seed.edifact_struktur_left_indent_position,
    )
    ahb_row_dataframe = esc.parse(ahb_row_dataframe=ahb_row_dataframe)

    # BODY
    boc = BodyCell(
        table_cell=middle_cell,
        left_indent_position=seed.middle_cell_left_indent_position,
        indicator_tabstop_positions=seed.tabstop_positions,
    )
    ahb_row_dataframe = boc.parse(ahb_row_dataframe=ahb_row_dataframe)

    # BEDINGUNG
    bec = BedingungCell(table_cell=bedingung_cell)
    ahb_row_dataframe = bec.parse(ahb_row_dataframe)

    return ahb_row_dataframe
