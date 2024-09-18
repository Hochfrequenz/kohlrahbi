"""
This module contains the AhbSubTable class.
"""

from typing import Generator

import pandas as pd
from docx.table import Table as DocxTable
from docx.table import _Cell, _Row
from pydantic import BaseModel, ConfigDict

from kohlrahbi.ahbtable.ahbtablerow import AhbTableRow
from kohlrahbi.docxtablecells import BedingungCell
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
        for row in docx_table.rows:
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
                ahb_table_row = AhbTableRow(
                    seed=table_meta_data,
                    edifact_struktur_cell=edifact_struktur_cell,
                    middle_cell=middle_cell,
                    bedingung_cell=bedingung_cell,
                )

                ahb_table_row_dataframe = ahb_table_row.parse(row_type=table_meta_data.last_two_row_types[1])
                if ahb_table_row_dataframe is not None:
                    ahb_table_dataframe = AhbSubTable.merge_with_last_row(ahb_table_dataframe, ahb_table_row_dataframe)
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
    def merge_with_last_row(ahb_table_dataframe: pd.DataFrame, ahb_table_row_dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Merges the last row of the dataframe with the current row.
        """
        # deal with the case of added conditions which will be added to the last condition block in the table
        contains_condition_texts = any(
            ahb_table_dataframe["Bedingung"].notna()
        )  # conditions are always at the top of a dataelement

        contains_beschreibung_but_no_qualifier = (
            ahb_table_row_dataframe["Beschreibung"][0] != "" and ahb_table_row_dataframe["Codes und Qualifier"][0] == ""
        )
        BESCHREIBUNG_INDEX = 6
        condition_does_not_start_with_operator = any(
            ahb_table_row_dataframe.iat[0, i]
            and not any(ahb_table_row_dataframe.iat[0, i].startswith(operator) for operator in CONDITIONS_OPERATORS)
            for i in range(BESCHREIBUNG_INDEX + 1, ahb_table_row_dataframe.shape[1] - 1)
        )  # check for cases with conditions which do not start with an operator like M, K, S, X (this also covers cases with "Muss" etc)
        last_condition_ends_incomplete = any(
            ahb_table_dataframe.iat[-1, i] and ahb_table_dataframe.iat[-1, i].endswith(" ")
            for i in range(BESCHREIBUNG_INDEX + 1, ahb_table_dataframe.shape[1] - 1)
        )
        is_empty_except_conditions_text = all(
            ahb_table_row_dataframe.at[0, column] == ""
            for column in ahb_table_row_dataframe.columns
            if column != "Bedingung"
        )
        is_broken_row = (
            contains_beschreibung_but_no_qualifier
            or condition_does_not_start_with_operator
            or last_condition_ends_incomplete
            or is_empty_except_conditions_text
        )

        # add condition texts
        if contains_condition_texts:
            conditions_text = " " + " ".join(
                ahb_table_row_dataframe["Bedingung"].apply(lambda x: x if x != "" else None).dropna()
            )
            last_valid_index = ahb_table_dataframe["Bedingung"].last_valid_index()
            conditions_text = ahb_table_dataframe.at[last_valid_index, "Bedingung"] + conditions_text
            conditions_text = BedingungCell.beautify_bedingungen(conditions_text)
            ahb_table_dataframe.at[last_valid_index, "Bedingung"] = conditions_text

        row = ahb_table_row_dataframe.iloc[0]
        # add broken row
        if is_broken_row:
            for column in ahb_table_row_dataframe[:-1]:
                add_text = row[column]
                is_empty_addtext = len(add_text) == 0
                is_empty_last_row_cell = len(ahb_table_dataframe[column].iloc[-1]) == 0
                if is_empty_addtext:
                    continue
                if not is_empty_last_row_cell:
                    add_text = " " + add_text
                ahb_table_dataframe.at[ahb_table_dataframe.index[-1], column] += add_text
        else:
            ahb_table_dataframe = pd.concat([ahb_table_dataframe, row], ignore_index=True)

        if ahb_table_row_dataframe.index.max() > 0:
            pd.concat([ahb_table_dataframe, ahb_table_row_dataframe.iloc[1:]], ignore_index=True)

        # for _, row in ahb_table_row_dataframe.iterrows():
        #    is_broken_row = True

        #   for column in ahb_table_row_dataframe:
        #      add_text = row[column]
        #     is_empty_addtext = len(add_text) == 0
        #    is_empty_last_row_cell = len(ahb_table_dataframe[column].iloc[-1]) == 0
        #   if is_empty_addtext:
        #      continue
        # if not is_empty_last_row_cell:
        #    add_text = " " + add_text
        # if column == "Bedingung":
        #    bedingung = ahb_table_dataframe[column].iloc[-1] + add_text
        #    bedingung = BedingungCell.beautify_bedingungen(bedingung)
        #    ahb_table_dataframe[column].iloc[-1] = bedingung
        # else:
        #    ahb_table_dataframe[column].iloc[-1] + add_text
        return ahb_table_dataframe
