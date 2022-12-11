"""
Collection of functions to write the extracted infos from the AHB tables into a DataFrame.
"""


from docx.table import Table, _Cell  # type:ignore[import]

from kohlrahbi.helper.row_type_checker import RowType
from kohlrahbi.helper.seed import Seed
from kohlrahbi.parser import parse_bedingung_cell, parse_edifact_struktur_cell, parse_middle_cell


def parse_ahb_row(
    seed: Seed, edifact_struktur_cell: _Cell, middle_cell: _Cell, bedingung_cell: _Cell, append_mode: bool
) -> None:
    """
    Writes all infos from a AHB table row into dataframe
    """

    if not append_mode:
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


def write_new_row_in_dataframe(
    elixir: Seed,
    row_type: RowType,
    ahb_table: Table,
    ahb_table_row: int,
    index_for_middle_column: int,
    append_mode: bool = False,
) -> None:
    """Writes the current row of the current table into the DataFrame depending on the type of the row

    Args:
        elixir (Elixir):
        row_type (RowType): Type of the current row
        table (Table): Current table
        index_for_middle_column (int): Index of the actual middle column
    """

    if row_type is RowType.HEADER:
        pass
    else:
        parse_ahb_row(
            seed=elixir,
            edifact_struktur_cell=ahb_table.row_cells(ahb_table_row)[0],
            middle_cell=ahb_table.row_cells(ahb_table_row)[index_for_middle_column],
            bedingung_cell=ahb_table.row_cells(ahb_table_row)[-1],
            append_mode=append_mode,
        )
