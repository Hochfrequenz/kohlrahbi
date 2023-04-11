"""
This module contains the UnfoldedAhbTable class.
"""

import json
import re
from pathlib import Path
from uuid import uuid4

import attrs
import pandas as pd
from maus.edifact import get_format_of_pruefidentifikator
from maus.models.anwendungshandbuch import (
    AhbLine,
    AhbMetaInformation,
    FlatAnwendungshandbuch,
    FlatAnwendungshandbuchSchema,
)
from maus.reader.flat_ahb_reader import FlatAhbCsvReader
from more_itertools import peekable

from kohlrahbi.ahb.ahbtable import AhbTable, _column_letter_width_mapping
from kohlrahbi.logger import logger
from kohlrahbi.unfoldedahb.unfoldedahbline import UnfoldedAhbLine
from kohlrahbi.unfoldedahb.unfoldedahbtablemetadata import UnfoldedAhbTableMetaData

_segment_group_pattern = re.compile(r"^SG\d+$")


@attrs.define(auto_attribs=True, kw_only=True)
class UnfoldedAhb:
    """
    The UnfoldedAhb contains one Prüfidentifikator.
    Some columns in the AHB documents contain multiple information in one column e.g. Segmentname and Segmentgruppe.
    The unfolded classes add new columns/attribues to avoid the duplication of information in one column.
    """

    meta_data: UnfoldedAhbTableMetaData
    unfolded_ahb_lines: list[UnfoldedAhbLine] = attrs.field(
        validator=attrs.validators.deep_iterable(member_validator=attrs.validators.instance_of(UnfoldedAhbLine))
    )

    @classmethod
    def from_ahb_table(cls, ahb_table: AhbTable, pruefi: str):
        """
        This function creates an UnfoldedAhb from an AhbTable.
        """
        unfolded_ahb_lines: list[UnfoldedAhbLine] = []
        current_section_name: str = ""

        # we need to peek one iteration in front of us
        iterable_ahb_table = peekable(ahb_table.table.iterrows())

        for index, series in enumerate(iterable_ahb_table):
            row = series[1]

            current_section_name = UnfoldedAhb._get_section_name(
                segment_gruppe_or_section_name=row["Segment Gruppe"], last_section_name=current_section_name
            )

            if UnfoldedAhb._is_section_name(ahb_row=row):
                _, next_row = iterable_ahb_table.peek()
                ahb_expression = next_row[pruefi]

                if _segment_group_pattern.match(next_row["Segment Gruppe"]):
                    segment_group_key = next_row["Segment Gruppe"]
                else:
                    segment_group_key = None

                unfolded_ahb_lines.append(
                    UnfoldedAhbLine(
                        index=index,
                        segment_name=current_section_name,
                        segment_gruppe=segment_group_key,
                        segment=None,
                        datenelement=None,
                        code=None,
                        qualifier=None,
                        beschreibung=None,
                        bedinung_ausdruck=ahb_expression or None,
                        bedingung=None,
                    )
                )
                continue

            if UnfoldedAhb._is_segment_group(ahb_row=row):
                value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
                    row["Codes und Qualifier"], row["Beschreibung"]
                )
                unfolded_ahb_lines.append(
                    UnfoldedAhbLine(
                        index=index,
                        segment_name=current_section_name,
                        segment_gruppe=row["Segment Gruppe"] or None,
                        segment=row["Segment"] or None,
                        datenelement=row["Datenelement"] or None,
                        code=value_pool_entry,
                        qualifier="",
                        beschreibung=description,
                        bedinung_ausdruck=row[pruefi] or None,
                        bedingung=row["Beschreibung"],
                    )
                )

            if UnfoldedAhb._is_segment_opening_line(ahb_row=row):
                unfolded_ahb_lines.append(
                    UnfoldedAhbLine(
                        index=index,
                        segment_name=current_section_name,
                        segment_gruppe=None,
                        segment=row["Segment"] or None,
                        datenelement=None,
                        code=None,
                        qualifier="",
                        beschreibung=None,
                        bedinung_ausdruck=row[pruefi] or None,
                        bedingung=row["Beschreibung"],
                    )
                )
                continue

            if UnfoldedAhb._is_just_segment(ahb_row=row):
                value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
                    row["Codes und Qualifier"], row["Beschreibung"]
                )
                unfolded_ahb_lines.append(
                    UnfoldedAhbLine(
                        index=index,
                        segment_name=current_section_name,
                        segment_gruppe=row["Segment Gruppe"] or None,
                        segment=row["Segment"] or None,
                        datenelement=row["Datenelement"] or None,
                        code=value_pool_entry,
                        qualifier="",
                        beschreibung=description,
                        bedinung_ausdruck=row[pruefi] or None,
                        bedingung=row["Beschreibung"],
                    )
                )
                continue

            if UnfoldedAhb._is_dataelement(ahb_row=row):
                value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
                    row["Codes und Qualifier"], row["Beschreibung"]
                )

                if _segment_group_pattern.match(row["Segment Gruppe"]):
                    segment_group_key = row["Segment Gruppe"]
                else:
                    segment_group_key = None

                unfolded_ahb_lines.append(
                    UnfoldedAhbLine(
                        index=index,
                        segment_name=current_section_name,
                        segment_gruppe=segment_group_key,
                        segment=row["Segment"] or None,
                        datenelement=row["Datenelement"] or None,
                        code=value_pool_entry,
                        qualifier="",
                        beschreibung=description,
                        bedinung_ausdruck=row[pruefi] or None,
                        bedingung=row["Beschreibung"],
                    )
                )
                continue

        return cls(
            unfolded_ahb_lines=unfolded_ahb_lines,
            meta_data=UnfoldedAhbTableMetaData(
                pruefidentifikator=pruefi,
            ),
        )

    @staticmethod
    def _get_section_name(segment_gruppe_or_section_name: str, last_section_name: str) -> str:
        """
        This function reads the section name if there is one.
        If the given string 'segment_gruppe_or_section_name' does not contain a section name,
        the 'last_section_name' will be returned.
        """
        if not (segment_gruppe_or_section_name.startswith("SG") or segment_gruppe_or_section_name == ""):
            return segment_gruppe_or_section_name
        return last_section_name

    @staticmethod
    def _is_section_name(ahb_row: pd.Series) -> bool:
        """
        Checks if the current AHB row is a section name.
        It uses the same logic as the function 'line_contains_only_segment_gruppe'
        So to avoid duplicate code, this function just calls the other function.
        """
        return AhbTable.line_contains_only_segment_gruppe(ahb_row)

    @staticmethod
    def _is_segment_group(ahb_row: pd.Series) -> bool:
        """Checks if the current AHB row is a segment group."""

        if _segment_group_pattern.match(ahb_row["Segment Gruppe"]) and not ahb_row["Segment"]:
            return True
        return False

    @staticmethod
    def _is_segment_opening_line(ahb_row: pd.Series) -> bool:
        """Checks if the current AHB row is a segment opening line.
        Example:

        SG3    CTA                                         Muss    Muss    Muss
        SG3    CTA    3139    IC    Informationskontakt    X       X       X

        The first line in the example is a segment opening line
        """

        if (
            _segment_group_pattern.match(ahb_row["Segment Gruppe"])
            and not ahb_row["Segment"]
            and ahb_row["Segment"]
            and not ahb_row["Datenelement"]
        ):
            return True
        return False

    @staticmethod
    def _is_just_segment(ahb_row: pd.Series) -> bool:
        """
        Checks if the given AHB row is a segment
        """

        if (
            _segment_group_pattern.match(ahb_row["Segment Gruppe"])
            and ahb_row["Segment"]
            and not ahb_row["Datenelement"]
        ):
            return True
        return False

    @staticmethod
    def _is_dataelement(ahb_row: pd.Series) -> bool:
        """
        Checks if the given AHB row is a dataelement
        """
        if ahb_row["Datenelement"]:
            return True
        return False

    def convert_to_flat_ahb(self) -> FlatAnwendungshandbuch:
        """
        Converts the unfolded AHB to a flat AHB.
        """
        meta = AhbMetaInformation(pruefidentifikator=self.meta_data.pruefidentifikator)
        lines: list[AhbLine] = []

        for unfolded_ahb_line in self.unfolded_ahb_lines:
            lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=unfolded_ahb_line.segment_gruppe,
                    segment_code=unfolded_ahb_line.segment,
                    data_element=unfolded_ahb_line.datenelement,
                    value_pool_entry=unfolded_ahb_line.code,
                    name=unfolded_ahb_line.beschreibung or unfolded_ahb_line.qualifier,
                    ahb_expression=unfolded_ahb_line.bedinung_ausdruck,
                    section_name=unfolded_ahb_line.segment_name,
                    index=unfolded_ahb_line.index,
                )
            )
        try:
            return FlatAnwendungshandbuch(meta=meta, lines=lines)
        except ValueError:
            logger.error(
                "Could not convert the unfolded AHB to a flat AHB for Prüfidentifikator '%s'",
                self.meta_data.pruefidentifikator,
            )
            raise

    def dump_flatahb_json(self, output_directory_path: Path) -> None:
        """
        Converts the unfolded AHB to a flat AHB and writes it to a json file.
        The file will be stored in the directory:
            'output_directory_path/<edifact_format>/flatahb/<pruefidentifikator>.json'
        """
        edifact_format = get_format_of_pruefidentifikator(self.meta_data.pruefidentifikator)
        if edifact_format is None:
            logger.warning("'%s' is not a pruefidentifikator", self.meta_data.pruefidentifikator)
            return

        flatahb_output_directory_path = output_directory_path / str(edifact_format) / "flatahb"
        flatahb_output_directory_path.mkdir(parents=True, exist_ok=True)

        dump_data = FlatAnwendungshandbuchSchema().dump(self.convert_to_flat_ahb())

        with open(
            flatahb_output_directory_path / f"{self.meta_data.pruefidentifikator}.json", "w", encoding="utf-8"
        ) as file:
            json.dump(dump_data, file, ensure_ascii=False, indent=2, sort_keys=True)
        logger.info(
            "The flatahb file for %s is saved at %s",
            self.meta_data.pruefidentifikator,
            flatahb_output_directory_path / f"{self.meta_data.pruefidentifikator}.json",
        )

    def convert_to_dataframe(self) -> pd.DataFrame:
        """
        Converts the unfolded AHB to a pandas dataframe.
        """
        unfolded_ahb_lines = [
            {
                "Segmentname": unfolded_ahb_line.segment_name,
                "Segmentgruppe": unfolded_ahb_line.segment_gruppe,
                "Segment": unfolded_ahb_line.segment,
                "Datenelement": unfolded_ahb_line.datenelement,
                "Code": unfolded_ahb_line.code,
                "Qualifier": unfolded_ahb_line.qualifier,
                "Beschreibung": unfolded_ahb_line.beschreibung,
                "Bedingungsausdruck": unfolded_ahb_line.bedinung_ausdruck,
                "Bedinung": unfolded_ahb_line.bedingung,
            }
            for unfolded_ahb_line in self.unfolded_ahb_lines
        ]

        df = pd.DataFrame(unfolded_ahb_lines)
        df.fillna(value="", inplace=True)
        return df

    def dump_csv(self, path_to_output_directory: Path) -> None:
        """
        Dump a UnfoldedAHB table into a csv file.
        The file will be stored in the directory:
            'path_to_output_directory/<edifact_format>/csv/<pruefidentifikator>.csv'
        """
        df = self.convert_to_dataframe()

        edifact_format = get_format_of_pruefidentifikator(self.meta_data.pruefidentifikator)
        if edifact_format is None:
            logger.warning("'%s' is not a pruefidentifikator", self.meta_data.pruefidentifikator)
            return

        csv_output_directory_path = path_to_output_directory / str(edifact_format) / "csv"
        csv_output_directory_path.mkdir(parents=True, exist_ok=True)

        df.to_csv(csv_output_directory_path / f"{self.meta_data.pruefidentifikator}.csv")
        logger.info(
            "The csv file for %s is saved at %s",
            self.meta_data.pruefidentifikator,
            csv_output_directory_path / f"{self.meta_data.pruefidentifikator}.csv",
        )

    def dump_xlsx(self, path_to_output_directory: Path) -> None:
        """
        Dump a AHB table of a given pruefi into an excel file.
        The file will be stored in the directory:
            'path_to_output_directory/<edifact_format>/xlsx/<pruefidentifikator>.xlsx'
        """
        edifact_format = get_format_of_pruefidentifikator(self.meta_data.pruefidentifikator)
        xlsx_output_directory_path: Path = path_to_output_directory / str(edifact_format) / "xlsx"
        xlsx_output_directory_path.mkdir(parents=True, exist_ok=True)

        excel_file_name = f"{self.meta_data.pruefidentifikator}.xlsx"

        df = self.convert_to_dataframe()

        try:
            # https://github.com/PyCQA/pylint/issues/3060
            # pylint: disable=abstract-class-instantiated
            with pd.ExcelWriter(xlsx_output_directory_path / excel_file_name, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name=f"{self.meta_data.pruefidentifikator}")
                # pylint: disable=no-member
                workbook = writer.book
                worksheet = writer.sheets[f"{self.meta_data.pruefidentifikator}"]
                wrap_format = workbook.add_format({"text_wrap": True})
                for column_letter, column_width in _column_letter_width_mapping.items():
                    excel_header = f"{column_letter}:{column_letter}"
                    worksheet.set_column(excel_header, column_width, wrap_format)
                logger.info("💾 Saved file(s) for Pruefidentifikator %s", self.meta_data.pruefidentifikator)
        except PermissionError:
            logger.error("The Excel file %s is open. Please close this file and try again.", excel_file_name)

        logger.info(
            "The xlsx file for %s is saved at %s",
            self.meta_data.pruefidentifikator,
            xlsx_output_directory_path / f"{self.meta_data.pruefidentifikator}.json",
        )
