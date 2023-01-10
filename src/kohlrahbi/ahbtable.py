"""
This module provides the AhbTable class
"""

from typing import Optional

import attrs
import pandas as pd
from docx.table import Table  # type:ignore[import]
from docx.table import _Cell

from kohlrahbi.ahbtablerow import AhbTableRow
from kohlrahbi.helper.row_type_checker import RowType, get_row_type
from kohlrahbi.helper.seed import Seed


@attrs.define(auto_attribs=True, kw_only=True)
class AhbTable:
    """
    This class contains the two attributes seed and table.
    Seed contains meta data about the ahb table like the left indent or which prüfis are in the current ahb table.
    The table is the read table from the docx file.
    """

    seed: Seed
    table: Table

    def _iter_visible_cells(self, row):
        """
        This function makes sure that you will iterate over the cells you see in the word document.
        For more information go to https://github.com/python-openxml/python-docx/issues/970#issuecomment-877386927
        """
        table_row = row._tr  # pylint:disable=protected-access
        for table_column in table_row.tc_lst:
            yield _Cell(table_column, row.table)

    def parse(self, ahb_table_dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Iterates through all rows of the AhbTable.table and writes all extracted infos in a DataFrame.

        Args:
            ahb_table_dataframe (pd.DataFrame): The dataframe which gets exported at the end.

        Returns:
            pd.DataFrame: Returns the ahb_table_dataframe with the added information.
        """

        for row in self.table.rows:

            sanitized_row = list(self._iter_visible_cells(row=row))

            current_edifact_struktur_cell = sanitized_row[0]

            # check for row type
            current_row_type = get_row_type(
                edifact_struktur_cell=current_edifact_struktur_cell,
                left_indent_position=self.seed.edifact_struktur_left_indent_position,
            )

            edifact_struktur_cell = sanitized_row[0]
            middle_cell = sanitized_row[1]
            bedingung_cell = sanitized_row[-1]

            # this case covers the "normal" docx table row
            if not (current_row_type is RowType.EMPTY and self.seed.last_two_row_types[0] is RowType.HEADER):

                ahb_table_row = AhbTableRow(
                    seed=self.seed,
                    edifact_struktur_cell=edifact_struktur_cell,
                    middle_cell=middle_cell,
                    bedingung_cell=bedingung_cell,
                )

                ahb_table_row_dataframe = ahb_table_row.parse(row_type=current_row_type)

                if ahb_table_dataframe is not None:
                    ahb_table_dataframe = pd.concat([ahb_table_dataframe, ahb_table_row_dataframe], ignore_index=True)
            # this case covers the page break situation
            else:

                ahb_table_row = AhbTableRow(
                    seed=self.seed,
                    edifact_struktur_cell=edifact_struktur_cell,
                    middle_cell=middle_cell,
                    bedingung_cell=bedingung_cell,
                )

                ahb_table_row.parse(row_type=self.seed.last_two_row_types[1])

            self.seed.last_two_row_types[1] = self.seed.last_two_row_types[0]
            self.seed.last_two_row_types[0] = current_row_type

        return ahb_table_dataframe

    @staticmethod
    def fill_segement_gruppe_segement_dataelement(df: pd.DataFrame):

        latest_segement_gruppe: Optional[str] = None
        latest_segement: Optional[str] = None
        latest_datenelement: Optional[str] = None

        for _, row in df.iterrows():

            if row["Segment Gruppe"] != "":
                latest_segement_gruppe: str = row["Segment Gruppe"]

            if row["Segment"] != "":
                latest_segement: str = row["Segment"]

            if row["Datenelement"] != "":
                latest_datenelement: str = row["Datenelement"]

            if row["Segment Gruppe"] == "" and row["Codes und Qualifier"] != "":
                row["Segment Gruppe"] = latest_segement_gruppe
                row["Segment"] = latest_segement
                row["Datenelement"] = latest_datenelement
