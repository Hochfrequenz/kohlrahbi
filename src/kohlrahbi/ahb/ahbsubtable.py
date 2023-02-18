"""
This module contains the AhbSubTable class.
"""

from typing import Generator

import attrs
import pandas as pd
from docx.table import Table as DocxTable  # type:ignore[import]
from docx.table import _Cell  # type:ignore[import]

from kohlrahbi.ahb.ahbtablerow import AhbTableRow
from kohlrahbi.row_type_checker import RowType, get_row_type
from kohlrahbi.seed import Seed


@attrs.define(auto_attribs=True, kw_only=True)
class AhbSubTable:
    """
    The AHB table for one Pruefidentifikator is separated into small sub tables.
    This class contains the information from such a sub table.
    """

    table_meta_data: Seed
    table: pd.DataFrame

    @staticmethod
    def _parse_docx_table(
        table_meta_data: Seed, ahb_table_dataframe: pd.DataFrame, docx_table: DocxTable
    ) -> pd.DataFrame:
        for row in docx_table.rows:
            sanitized_cells = list(AhbSubTable._iter_visible_cells(row=row))

            current_edifact_struktur_cell = sanitized_cells[0]

            # check for row type
            current_row_type = get_row_type(
                edifact_struktur_cell=current_edifact_struktur_cell,
                left_indent_position=table_meta_data.edifact_struktur_left_indent_position,
            )

            edifact_struktur_cell = sanitized_cells[0]
            middle_cell = sanitized_cells[1]
            bedingung_cell = sanitized_cells[-1]

            # this case covers the "normal" docx table row
            if not (current_row_type is RowType.EMPTY and table_meta_data.last_two_row_types[0] is RowType.HEADER):
                ahb_table_row = AhbTableRow(
                    seed=table_meta_data,
                    edifact_struktur_cell=edifact_struktur_cell,
                    middle_cell=middle_cell,
                    bedingung_cell=bedingung_cell,
                )

                ahb_table_row_dataframe = ahb_table_row.parse(row_type=current_row_type)

                if ahb_table_row_dataframe is not None:
                    ahb_table_dataframe = pd.concat([ahb_table_dataframe, ahb_table_row_dataframe], ignore_index=True)
            # this case covers the page break situation
            else:
                ahb_table_row = AhbTableRow(
                    seed=table_meta_data,
                    edifact_struktur_cell=edifact_struktur_cell,
                    middle_cell=middle_cell,
                    bedingung_cell=bedingung_cell,
                )

                ahb_table_row.parse(row_type=table_meta_data.last_two_row_types[1])

            # An AhbSubTable can span over two pages.
            # But after every page break, even if we're still in the same subtable,
            # there'll be the header at the top of every page.
            # This distracts our detection logic but we workaround it by remembering
            # the last two row types.
            table_meta_data.last_two_row_types[1] = table_meta_data.last_two_row_types[0]
            table_meta_data.last_two_row_types[0] = current_row_type
        return ahb_table_dataframe

    @staticmethod
    def initialize_dataframe_with_columns(columns: list[str]) -> pd.DataFrame:
        """
        Initialize a new dataframe with the given columns
        """
        return pd.DataFrame(
            columns=columns,
            dtype="str",
        )

    @classmethod
    def from_table_with_header(cls, docx_table: DocxTable) -> "AhbSubTable":
        """
        Create a new AhbSubTable instance from a docx table WITH header
        """

        ahb_table_meta_data = Seed.from_table(docx_table=docx_table)

        ahb_table_dataframe = AhbSubTable.initialize_dataframe_with_columns(columns=ahb_table_meta_data.column_headers)

        ahb_table_dataframe = cls._parse_docx_table(
            table_meta_data=ahb_table_meta_data,
            ahb_table_dataframe=ahb_table_dataframe,
            docx_table=docx_table,
        )

        return cls(table_meta_data=ahb_table_meta_data, table=ahb_table_dataframe)

    @classmethod
    def from_headless_table(cls, tmd: Seed, docx_table: DocxTable) -> "AhbSubTable":
        """
        Create a new AhbSubTable instance from a docx table WITHOUT header
        """

        ahb_table_dataframe = AhbSubTable.initialize_dataframe_with_columns(columns=tmd.column_headers)

        ahb_table_dataframe = cls._parse_docx_table(
            table_meta_data=tmd,
            ahb_table_dataframe=ahb_table_dataframe,
            docx_table=docx_table,
        )

        return cls(table_meta_data=tmd, table=ahb_table_dataframe)

    @staticmethod
    def _iter_visible_cells(row) -> Generator[_Cell, None, None]:
        """
        This function makes sure that you will iterate over the cells you see in the word document.
        For more information go to https://github.com/python-openxml/python-docx/issues/970#issuecomment-877386927
        """
        table_row = row._tr  # pylint:disable=protected-access
        for table_column in table_row.tc_lst:
            yield _Cell(table_column, row.table)
