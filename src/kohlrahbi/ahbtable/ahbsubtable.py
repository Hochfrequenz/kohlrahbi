"""
This module contains the AhbSubTable class.
"""

from itertools import chain
from typing import Generator

import pandas as pd
from docx.table import Table as DocxTable
from docx.table import _Cell, _Row
from more_itertools import windowed
from pydantic import BaseModel, ConfigDict

from kohlrahbi.ahbtable.ahbtablerow import AhbTableRow
from kohlrahbi.docxtablecells import BedingungCell
from kohlrahbi.docxtablecells.bodycell import KNOW_SUFFIXES
from kohlrahbi.enums import RowType
from kohlrahbi.row_type_checker import get_row_type
from kohlrahbi.seed import Seed

CONDITIONS_OPERATORS = ["M", "K", "S", "X"]


class AhbSubTable(BaseModel):
    """
    The AHB table for one Pruefidentifikator is separated into small sub tables.
    This class contains the information from such a sub table.
    """

    table_meta_data: Seed
    table: pd.DataFrame

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    def _parse_docx_table(
        table_meta_data: Seed, ahb_table_dataframe: pd.DataFrame, docx_table: DocxTable
    ) -> pd.DataFrame:
        for last_last_row, last_row, row in windowed(chain([None, None], docx_table.rows), 3):  # docx_table.rows:
            sanitized_cells = list(AhbSubTable.iter_visible_cells(row=row))

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
                # check last_last row for left indent
                last_last_sanitized_cells = list(AhbSubTable.iter_visible_cells(row=last_last_row))
                last_last_middle_cell = last_last_sanitized_cells[1]

                ### check for broken lines
                contains_condition_texts = any(paragraph.text != "" for paragraph in bedingung_cell.paragraphs)
                # conditions are always at the top of a dataelement

                number_of_pruefi_columns = len(table_meta_data.pruefidentifikatoren)
                beschreibung_index = ahb_table_dataframe.columns.get_loc("Beschreibung")
                min_row_index_to_add = 0
                # add condition texts
                if contains_condition_texts:
                    AhbSubTable.add_condition_text(ahb_table_dataframe, bedingung_cell)
                # loop over all lines in middle cell to fix broken lines
                for paragraph in middle_cell.paragraphs:
                    row_tablsplit = paragraph.text.split("\t")
                    is_empty_line, are_only_conditions_in_row, is_left_indent_different, is_broken_line = (
                        AhbSubTable.check_broken_lines(
                            previous_cell=last_last_middle_cell,
                            table_meta_data=table_meta_data,
                            paragraph=paragraph,
                            tabsplit_text=row_tablsplit,
                            current_row_type=current_row_type,
                            number_of_pruefi_columns=number_of_pruefi_columns,
                        )
                    )

                    is_empty_line = all(text == "" for text in row_tablsplit)
                    are_only_conditions_in_row = (
                        current_row_type == RowType.EMPTY
                        and any(text != "" for text in row_tablsplit[-number_of_pruefi_columns:])
                        and all(text == "" for text in row_tablsplit[:-number_of_pruefi_columns])
                    )
                    is_left_indent_different = (
                        paragraph.paragraph_format.left_indent
                        != last_last_middle_cell.paragraphs[-1].paragraph_format.left_indent
                        and paragraph.paragraph_format.left_indent != table_meta_data.middle_cell_left_indent_position
                    )
                    is_broken_line = are_only_conditions_in_row or is_left_indent_different or is_empty_line
                    if is_broken_line:
                        min_row_index_to_add = 1

                    if is_left_indent_different and not are_only_conditions_in_row and not is_empty_line:
                        assert (
                            len(row_tablsplit) == number_of_pruefi_columns + 1
                        ), "more tabsplits than expected for broken row"
                        AhbSubTable.add_text_to_last_row(ahb_table_dataframe, -1, beschreibung_index, row_tablsplit[0])

                    if are_only_conditions_in_row or is_left_indent_different:
                        # add conditions
                        for index, condition in enumerate(row_tablsplit[-number_of_pruefi_columns:]):
                            AhbSubTable.add_text_to_last_row(
                                ahb_table_dataframe, -1, beschreibung_index + index + 1, condition
                            )
                    else:
                        # add new row regularly
                        ahb_table_row = AhbTableRow(
                            seed=table_meta_data,
                            edifact_struktur_cell=edifact_struktur_cell,
                            middle_cell=middle_cell,
                            bedingung_cell=bedingung_cell,
                        )
                        ahb_table_row_dataframe = ahb_table_row.parse(row_type=current_row_type)
                        if ahb_table_row_dataframe is not None:
                            ahb_table_row_dataframe["Bedingung"] = ""
                            if ahb_table_row_dataframe.index.max() > 0:
                                ahb_table_dataframe = pd.concat(
                                    [ahb_table_dataframe, ahb_table_row_dataframe.iloc[min_row_index_to_add:]],
                                    ignore_index=True,
                                )
                        break

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
    def iter_visible_cells(row: _Row) -> Generator[_Cell, None, None]:
        """
        This function makes sure that you will iterate over the cells you see in the word document.
        For more information go to https://github.com/python-openxml/python-docx/issues/970#issuecomment-877386927
        """
        table_row = row._tr  # pylint:disable=protected-access
        for table_column in table_row.tc_lst:
            yield _Cell(table_column, row.table)

    @staticmethod
    def add_text_to_last_row(ahb_table_dataframe: pd.DataFrame, row_index: int, column_index: int, text: str) -> None:
        starts_with_known_suffix = any(text.startswith(suffix) for suffix in KNOW_SUFFIXES)
        if len(text) > 0:
            if len(ahb_table_dataframe.iat[row_index, column_index]) > 0 and not starts_with_known_suffix:
                text = " " + text
            ahb_table_dataframe.iat[row_index, column_index] += text

    @staticmethod
    def add_condition_text(ahb_table_dataframe: pd.DataFrame, bedingung_cell: _Cell) -> None:
        conditions_text = " " + " ".join(
            paragraph.text for paragraph in bedingung_cell.paragraphs if paragraph.text != ""
        )
        last_valid_index = ahb_table_dataframe["Bedingung"].last_valid_index()
        conditions_text = ahb_table_dataframe.at[last_valid_index, "Bedingung"] + conditions_text
        conditions_text = BedingungCell.beautify_bedingungen(conditions_text)
        ahb_table_dataframe.at[last_valid_index, "Bedingung"] = conditions_text

    @staticmethod
    def check_broken_lines(
        previous_cell: _Cell,
        table_meta_data: Seed,
        paragraph: _Cell,
        tabsplit_text: list[str],
        current_row_type: RowType,
        number_of_pruefi_columns: int,
    ) -> tuple[bool, bool, bool, bool]:
        """
        Check for broken lines in the middle cell
        """
        is_empty_line = all(text == "" for text in tabsplit_text)
        are_only_conditions_in_row = (
            current_row_type == RowType.EMPTY
            and any(text != "" for text in tabsplit_text[-number_of_pruefi_columns:])
            and all(text == "" for text in tabsplit_text[:-number_of_pruefi_columns])
        )
        is_left_indent_different = (
            paragraph.paragraph_format.left_indent != previous_cell.paragraphs[-1].paragraph_format.left_indent
            and paragraph.paragraph_format.left_indent != table_meta_data.middle_cell_left_indent_position
        )
        is_broken_line = are_only_conditions_in_row or is_left_indent_different or is_empty_line

        return is_empty_line, are_only_conditions_in_row, is_left_indent_different, is_broken_line
