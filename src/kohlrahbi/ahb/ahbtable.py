"""
This module provides the AhbTable class
"""
from pathlib import Path
from typing import Union

import attrs
import pandas as pd
from maus.edifact import get_format_of_pruefidentifikator
from more_itertools import peekable

from kohlrahbi.ahb.ahbsubtable import AhbSubTable
from kohlrahbi.logger import logger
from kohlrahbi.table_header import PruefiMetaData

_column_letter_width_mapping: dict[str, Union[float, int]] = {
    "A": 3.5,
    "B": 47,
    "C": 9,
    "D": 14,
    "E": 39,
    "F": 33,
    "G": 18,
    "H": 102,
}


@attrs.define(auto_attribs=True, kw_only=True)
class AhbTable:
    """
    This class contains the AHB table as you see it in the AHB documents, but in a machine readable format.
    """

    table: pd.DataFrame
    metadata: list[PruefiMetaData] = []

    def fill_segment_gruppe_segment_dataelement(self) -> None:
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

        latest_segement_gruppe: str = ""
        latest_segement: str = ""
        latest_datenelement: str = ""

        for _, row in self.table.iterrows():
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
    def from_ahb_sub_table(cls, ahb_sub_table: AhbSubTable) -> "AhbTable":
        """
        Create an AHB table from an AHB sub table
        """
        return cls(table=ahb_sub_table.table, metadata=ahb_sub_table.table_meta_data.metadata)

    def append_ahb_sub_table(self, ahb_sub_table: AhbSubTable) -> None:
        """
        Append an AHB sub table to this AHB table instance
        """
        if self.table is None:
            self.table = ahb_sub_table.table
        else:
            self.table = pd.concat([self.table, ahb_sub_table.table], ignore_index=True)

    @staticmethod
    def line_contains_only_segment_gruppe(raw_line: pd.Series) -> bool:
        """
        Returns true if the given raw line only contains some meaningful data in the "Segment Gruppe" key
        """
        for key, value in raw_line.items():
            if key == "Segment Gruppe":
                continue
            if value is not None and len(value.strip()) > 0:
                return False
        return True

    def sanitize(self) -> None:
        """
        In some cases there is the content of one cell splitted in two.
        We need to merge the content into one cell and delete the deprecated cell afterwards.
        """
        index_of_lines_to_drop: list[int] = []

        iterable_ahb_table = peekable(self.table.iterrows())
        self.table.reset_index(drop=True, inplace=True)
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

            segment_gruppe_contains_multiple_lines = (
                "Segment Gruppe" in row
                and row["Segment Gruppe"]
                and AhbTable.line_contains_only_segment_gruppe(row)
                and not next_row["Segment Gruppe"].startswith("SG")
                and not next_row["Segment"]
            )
            if segment_gruppe_contains_multiple_lines:
                merged_segment_gruppe_content = " ".join([row["Segment Gruppe"], next_row["Segment Gruppe"]])
                row["Segment Gruppe"] = merged_segment_gruppe_content.strip()

                if not isinstance(index_of_next_row, int):
                    raise TypeError(
                        f"The 'index_of_next_row' must by of type `int` but it is '{type(index_of_next_row)}'"
                    )

                if index_of_next_row == 0:
                    # this case is only for the first and last row. These lines should not get deleted.
                    continue
                index_of_lines_to_drop.append(index_of_next_row)

        self.table.drop(index_of_lines_to_drop, inplace=True)
        self.table.reset_index(drop=True, inplace=True)

    def to_csv(self, pruefi: str, path_to_output_directory: Path) -> None:
        """
        Dump an AHB table of a given pruefi into a csv file.
        The csv file will be saved in the following directory structure:
            <path_to_output_directory>/csv/<edifact_format>/<pruefi>.csv
        """
        edifact_format = get_format_of_pruefidentifikator(pruefi)
        if edifact_format is None:
            logger.warning("'%s' is not a pruefidentifikator", pruefi)
            return

        csv_output_directory_path = path_to_output_directory / "csv" / str(edifact_format)
        csv_output_directory_path.mkdir(parents=True, exist_ok=True)

        self.fill_segment_gruppe_segment_dataelement()

        columns_to_export = list(self.table.columns)[:5] + [pruefi]
        columns_to_export.append("Bedingung")
        df_to_export = self.table[columns_to_export]

        df_to_export.to_csv(csv_output_directory_path / f"{pruefi}.csv")
        logger.info("The csv file for %s is saved at %s", pruefi, csv_output_directory_path / f"{pruefi}.csv")

    # pylint: disable=too-many-locals
    def to_xlsx(self, pruefi: str, path_to_output_directory: Path) -> None:
        """
        Dump a AHB table of a given pruefi into an excel file.
        The excel file will be saved in the following directory structure:
            <path_to_output_directory>/xlsx/<edifact_format>/<pruefi>.xlsx
        """
        edifact_format = get_format_of_pruefidentifikator(pruefi)
        if edifact_format is None:
            logger.warning("'%s' is not a pruefidentifikator", pruefi)
            return

        xlsx_output_directory_path: Path = path_to_output_directory / "xlsx" / str(edifact_format)
        xlsx_output_directory_path.mkdir(parents=True, exist_ok=True)

        excel_file_name = f"{pruefi}.xlsx"

        columns_to_export = list(self.table.columns)[:5] + [pruefi]
        columns_to_export.append("Bedingung")
        df_to_export = self.table[columns_to_export]

        try:
            # https://github.com/PyCQA/pylint/issues/3060 pylint: disable=abstract-class-instantiated
            with pd.ExcelWriter(xlsx_output_directory_path / excel_file_name, engine="xlsxwriter") as writer:
                df_to_export.to_excel(writer, sheet_name=f"{pruefi}")
                # pylint: disable=no-member
                workbook = writer.book
                worksheet = writer.sheets[f"{pruefi}"]
                wrap_format = workbook.add_format({"text_wrap": True})
                for column_letter, column_width in _column_letter_width_mapping.items():
                    excel_header = f"{column_letter}:{column_letter}"
                    worksheet.set_column(excel_header, column_width, wrap_format)
                logger.info("💾 Saved file(s) for Pruefidentifikator %s", pruefi)
        except PermissionError:
            logger.error("The Excel file %s is open. Please close this file and try again.", excel_file_name)
