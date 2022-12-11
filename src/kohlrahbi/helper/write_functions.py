"""
Collection of functions to write the extracted infos from the AHB tables into a DataFrame.
"""


from docx.table import Table, _Cell  # type:ignore[import]

from kohlrahbi.helper.row_type_checker import RowType
from kohlrahbi.helper.seed import Seed
from kohlrahbi.parser import parse_bedingung_cell, parse_edifact_struktur_cell, parse_middle_cell


def parse_ahb_table_row(
    seed: Seed,
    row_type: RowType,
    ahb_table: Table,
    ahb_table_row: int,
    index_for_middle_column: int,
    is_appending: bool = False,
) -> None:
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

    edifact_struktur_cell = ahb_table.row_cells(ahb_table_row)[0]
    middle_cell = ahb_table.row_cells(ahb_table_row)[index_for_middle_column]
    bedingung_cell = ahb_table.row_cells(ahb_table_row)[-1]

    if not is_appending:
        seed.soul.loc[seed.soul.index.max() + 1, :] = ""

    # EDIFACT STRUKTUR COLUMN
    parse_edifact_struktur_cell(
        table_cell=edifact_struktur_cell,
        dataframe=seed.soul,
        edifact_struktur_cell_left_indent_position=seed.edifact_struktur_left_indent_position,
    )

    # MIDDLE COLUMN
    parse_middle_cell(
        table_cell=middle_cell,
        dataframe=seed.soul,
        left_indent_position=seed.middle_cell_left_indent_position,
        indicator_tabstop_positions=seed.tabstop_positions,
    )

    # BEDINGUNG COLUMN
    parse_bedingung_cell(
        bedingung_cell=bedingung_cell,
        dataframe=seed.soul,
    )
