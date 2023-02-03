"""
This module provides the AhbTable class
"""

from typing import Optional

import attrs
import pandas as pd
from docx.table import Table  # type:ignore[import]
from docx.table import _Cell
from more_itertools import peekable

from kohlrahbi.ahbsubtable import AhbSubTable
from kohlrahbi.ahbtablerow import AhbTableRow
from kohlrahbi.dump.flatahb import keys_that_must_no_hold_any_values
from kohlrahbi.row_type_checker import RowType, get_row_type
from kohlrahbi.seed import Seed


@attrs.define(auto_attribs=True, kw_only=True)
class NewAhbTable:
    """
    This class contains the docx table and class with the table meta data.
    Seed contains meta data about the ahb table like the left indent or which prüfis are in the current ahb table.
    The table is the read table from the docx file.
    """

    table: pd.DataFrame

    @staticmethod
    def fill_segement_gruppe_segement_dataelement(df: pd.DataFrame):
        """
        For easier readability this functions adds the segment

        before
        ======

        Nachrichten-Kopfsegment
                                    UNH
                                    UNH    0062

        after
        =====

        Nachrichten-Kopfsegment
        Nachrichten-Kopfsegment     UNH
        Nachrichten-Kopfsegment     UNH    0062
        """

        latest_segement_gruppe: Optional[str] = ""
        latest_segement: Optional[str] = ""
        latest_datenelement: Optional[str] = ""

        for _, row in df.iterrows():
            if row["Segment Gruppe"] != "":
                latest_segement_gruppe = row["Segment Gruppe"]

            if row["Segment"] != "":
                latest_segement = row["Segment"]

            if row["Datenelement"] != "":
                latest_datenelement = row["Datenelement"]

            if row["Segment Gruppe"] == "" and row["Codes und Qualifier"] != "" or row["Segment"] != "":
                row["Segment Gruppe"] = latest_segement_gruppe
                row["Segment"] = latest_segement
                row["Datenelement"] = latest_datenelement

    @classmethod
    def from_ahb_sub_table(cls, ahb_sub_table: AhbSubTable):
        return cls(table=ahb_sub_table.table)

    def append_ahb_sub_table(self, ahb_sub_table: AhbSubTable):
        if self.table is None:
            self.table = ahb_sub_table.table
        else:
            self.table = pd.concat([self.table, ahb_sub_table.table], ignore_index=True)

    def sanitize(self):
        """
        In some cases there is the content of one cell splitted in two.
        We need to merge the content into one cell and delete the deprecated cell afterwards.
        """
        lines_to_drop: list[int] = []

        def line_contains_only_segment_gruppe(raw_line: pd.Series) -> bool:
            """
            returns true if the given raw line only contains some meaningful data in the "Segment Gruppe" key
            """
            for row_key in keys_that_must_no_hold_any_values:
                if row_key in raw_line and raw_line[row_key] is not None and len(raw_line[row_key].strip()) > 0:
                    return False
            return True

        iterable_ahb_table = peekable(self.table.iterrows())

        for _, row in iterable_ahb_table:
            index_of_next_row, next_row = iterable_ahb_table.peek(
                (
                    0,
                    pd.Series(
                        {
                            "Segment Gruppe": "",
                            "Segment": "",
                            "Codes und Qualifier": "",
                            "Beschreibung": "",
                            "Bedingung": "",
                        }
                    ),
                )
            )

            # TODO put the condition into a meaningful bool variable
            if (
                "Segment Gruppe" in row
                and row["Segment Gruppe"]
                and line_contains_only_segment_gruppe(row)
                and not next_row["Segment Gruppe"].startswith("SG")
                and not next_row["Segment"]
            ):
                merged_segment_gruppe_content = " ".join([row["Segment Gruppe"], next_row["Segment Gruppe"]])
                row["Segment Gruppe"] = merged_segment_gruppe_content.strip()

                if isinstance(index_of_next_row, int):
                    if index_of_next_row == 0:
                        # this case is only for the first and last row. These lines should not get deleted.
                        continue
                    lines_to_drop.append(index_of_next_row)
                else:
                    raise TypeError(
                        f"The 'index_of_next_row' must by of type `int` but it is '{type(index_of_next_row)}'"
                    )

        self.table.drop(lines_to_drop)
        self.table.reset_index(drop=True)
