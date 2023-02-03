"""
This module provides the AhbTable class
"""
import re
from pathlib import Path
from typing import Optional, Union

import attrs
import pandas as pd
from maus.edifact import get_format_of_pruefidentifikator
from more_itertools import peekable

from kohlrahbi.ahbsubtable import AhbSubTable
from kohlrahbi.logger import logger

keys_that_must_no_hold_any_values: set[str] = {
    "Segment",
    "Datenelement",
    "Codes und Qualifier",
    "Beschreibung",
    "Bedingung",
}

_segment_group_pattern = re.compile(r"^SG\d+$")


@attrs.define(auto_attribs=True, kw_only=True)
class NewAhbTable:
    """
    This class contains the docx table and class with the table meta data.
    Seed contains meta data about the ahb table like the left indent or which prüfis are in the current ahb table.
    The table is the read table from the docx file.
    """

    table: pd.DataFrame

    def fill_segement_gruppe_segement_dataelement(self):
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
    def from_ahb_sub_table(cls, ahb_sub_table: AhbSubTable):
        return cls(table=ahb_sub_table.table)

    def append_ahb_sub_table(self, ahb_sub_table: AhbSubTable):
        """
        Append an AHB sub table to the AHB table
        """
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

        self.table.drop(lines_to_drop, inplace=True)
        self.table.reset_index(drop=True)

    def to_csv(self, pruefi: str, path_to_output_directory: Path):
        """
        Dump a AHB table of a given pruefi into a csv file.
        """
        edifact_format = get_format_of_pruefidentifikator(pruefi)
        if edifact_format is None:
            logger.warning("'%s' is not a pruefidentifikator", pruefi)
            return

        csv_output_directory_path = path_to_output_directory / "csv" / str(edifact_format)
        csv_output_directory_path.mkdir(parents=True, exist_ok=True)

        self.fill_segement_gruppe_segement_dataelement()

        columns_to_export = list(self.table.columns)[:5] + [pruefi]
        columns_to_export.append("Bedingung")
        df_to_export = self.table[columns_to_export]

        df_to_export.to_csv(csv_output_directory_path / f"{pruefi}.csv")
        logger.info("The csv file for %s is saved at %s", pruefi, csv_output_directory_path / f"{pruefi}.csv")

    def to_xlsx(self, pruefi: str, path_to_output_directory: Path):
        """
        Dump a AHB table of a given pruefi into an excel file.
        """
        edifact_format = get_format_of_pruefidentifikator(pruefi)
        xlsx_output_directory_path: Path = path_to_output_directory / "xlsx" / str(edifact_format)
        xlsx_output_directory_path.mkdir(parents=True, exist_ok=True)

        excel_file_name = f"{pruefi}.xlsx"

        columns_to_export = list(self.table.columns)[:5] + [pruefi]
        columns_to_export.append("Bedingung")
        df_to_export = self.table[columns_to_export]

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
                logger.info("💾 Saved files for Pruefidentifikator %s", pruefi)
        except PermissionError:
            logger.error("The Excel file %s is open. Please close this file and try again.", excel_file_name)

    # @staticmethod
    # def _get_section_name(segment_gruppe_or_section_name: str, last_section_name: str) -> str:
    #     """
    #     This function reads the section name if there is one.
    #     If the given string 'segment_gruppe_or_section_name' does not contain a section name,
    #     the 'last_section_name' will be returned.
    #     """
    #     if not (segment_gruppe_or_section_name.startswith("SG") or segment_gruppe_or_section_name == ""):
    #         return segment_gruppe_or_section_name
    #     return last_section_name

    # @staticmethod
    # def _is_section_name(ahb_row: pd.Series) -> bool:
    #     """
    #     Checks if the current AHB row is a section name.
    #     """

    #     for row_key in keys_that_must_no_hold_any_values:
    #         if ahb_row[row_key]:
    #             return False
    #     return True

    # @staticmethod
    # def _is_segment_group(ahb_row: pd.Series) -> bool:
    #     """Checks if the current AHB row is a segment group."""

    #     if _segment_group_pattern.match(ahb_row["Segment Gruppe"]) and not ahb_row["Segment"]:
    #         return True
    #     return False

    # @staticmethod
    # def _is_segment_opening_line(ahb_row: pd.Series) -> bool:
    #     """Checks if the current AHB row is a segment opening line.
    #     Example:

    #     SG3    CTA                                         Muss    Muss    Muss
    #     SG3    CTA    3139    IC    Informationskontakt    X       X       X

    #     The first line in the example is a segment opening line
    #     """

    #     if (
    #         _segment_group_pattern.match(ahb_row["Segment Gruppe"])
    #         and not ahb_row["Segment"]
    #         and ahb_row["Segment"]
    #         and not ahb_row["Datenelement"]
    #     ):
    #         return True
    #     return False

    # @staticmethod
    # def _is_just_segment(ahb_row: pd.Series) -> bool:
    #     """
    #     Checks if the given AHB row is a segment
    #     """

    #     if (
    #         _segment_group_pattern.match(ahb_row["Segment Gruppe"])
    #         and ahb_row["Segment"]
    #         and not ahb_row["Datenelement"]
    #     ):
    #         return True
    #     return False

    # @staticmethod
    # def _is_dataelement(ahb_row: pd.Series) -> bool:
    #     """
    #     Checks if the given AHB row is a dataelement
    #     """
    #     if ahb_row["Datenelement"]:
    #         return True
    #     return False

    # def convert_to_flat_ahb(self, pruefi: str):
    #     """
    #     Convert a AHB table of a given pruefi into as FlatAHB instance.
    #     """
    #     ahb_lines: list[AhbLine] = []
    #     index = 0
    #     current_section_name: str = ""

    #     iterable_ahb_table = peekable(self.table.iterrows())

    #     for _, row in iterable_ahb_table:
    #         current_section_name = NewAhbTable._get_section_name(
    #             segment_gruppe_or_section_name=row["Segment Gruppe"], last_section_name=current_section_name
    #         )

    #         if NewAhbTable._is_section_name(ahb_row=row):
    #             _, next_row = iterable_ahb_table.peek()
    #             ahb_expression = next_row[pruefi]

    #             if _segment_group_pattern.match(next_row["Segment Gruppe"]):
    #                 segment_group_key = next_row["Segment Gruppe"]
    #             else:
    #                 segment_group_key = None

    #             ahb_lines.append(
    #                 AhbLine(
    #                     guid=uuid4(),
    #                     segment_group_key=segment_group_key,
    #                     segment_code=None,
    #                     data_element=None,
    #                     value_pool_entry=None,
    #                     name=None,
    #                     ahb_expression=ahb_expression or None,
    #                     section_name=current_section_name,
    #                     index=index,
    #                 )
    #             )
    #             index = index + 1
    #             continue

    #         if NewAhbTable._is_segment_group(ahb_row=row):
    #             value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
    #                 row["Codes und Qualifier"], row["Beschreibung"]
    #             )
    #             ahb_lines.append(
    #                 AhbLine(
    #                     guid=uuid4(),
    #                     segment_group_key=row["Segment Gruppe"] or None,
    #                     segment_code=row["Segment"] or None,
    #                     data_element=row["Datenelement"] or None,
    #                     value_pool_entry=value_pool_entry,
    #                     name=description,
    #                     ahb_expression=row[pruefi] or None,
    #                     section_name=current_section_name,
    #                     index=index,
    #                 )
    #             )

    #         if NewAhbTable._is_segment_opening_line(ahb_row=row):
    #             ahb_lines.append(
    #                 AhbLine(
    #                     guid=uuid4(),
    #                     segment_group_key=None,
    #                     segment_code=row["Segment"] or None,
    #                     data_element=None,
    #                     value_pool_entry=None,
    #                     name=None,
    #                     ahb_expression=row[pruefi] or None,
    #                     section_name=current_section_name,
    #                     index=index,
    #                 )
    #             )
    #             index = index + 1
    #             continue

    #         if NewAhbTable._is_just_segment(ahb_row=row):
    #             value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
    #                 row["Codes und Qualifier"], row["Beschreibung"]
    #             )
    #             ahb_lines.append(
    #                 AhbLine(
    #                     guid=uuid4(),
    #                     segment_group_key=row["Segment Gruppe"] or None,
    #                     segment_code=row["Segment"] or None,
    #                     data_element=row["Datenelement"] or None,
    #                     value_pool_entry=value_pool_entry,
    #                     name=description,
    #                     ahb_expression=row[pruefi] or None,
    #                     section_name=current_section_name,
    #                     index=index,
    #                 )
    #             )
    #             index = index + 1
    #             continue

    #         if NewAhbTable._is_dataelement(ahb_row=row):
    #             value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
    #                 row["Codes und Qualifier"], row["Beschreibung"]
    #             )

    #             if _segment_group_pattern.match(row["Segment Gruppe"]):
    #                 segment_group_key = row["Segment Gruppe"]
    #             else:
    #                 segment_group_key = None

    #             ahb_lines.append(
    #                 AhbLine(
    #                     guid=uuid4(),
    #                     segment_group_key=segment_group_key,
    #                     segment_code=row["Segment"] or None,
    #                     data_element=row["Datenelement"] or None,
    #                     value_pool_entry=value_pool_entry,
    #                     name=description,
    #                     ahb_expression=row[pruefi] or None,
    #                     section_name=current_section_name,
    #                     index=index,
    #                 )
    #             )
    #             index = index + 1
    #             continue

    #     ahb_meta_information: AhbMetaInformation = AhbMetaInformation(pruefidentifikator=pruefi)

    #     return FlatAnwendungshandbuch(meta=ahb_meta_information, lines=ahb_lines)
