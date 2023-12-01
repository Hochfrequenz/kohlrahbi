"""
This module contains the UnfoldedAhbTable class.
"""
import copy
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
from more_itertools import first_true, peekable

from kohlrahbi.ahb.ahbtable import AhbTable, _column_letter_width_mapping
from kohlrahbi.logger import logger
from kohlrahbi.unfoldedahb.unfoldedahbline import UnfoldedAhbLine
from kohlrahbi.unfoldedahb.unfoldedahbtablemetadata import UnfoldedAhbTableMetaData

_segment_group_pattern = re.compile(r"^SG\d+$")


def _lines_are_equal_when_ignoring_guid(line1: AhbLine, line2: AhbLine) -> bool:
    """
    returns true iff the line1 and line2 are equal except for their guid
    """
    line1_copy = copy.deepcopy(line1)
    line2_copy = copy.deepcopy(line2)
    line1_copy.guid = None
    line2_copy.guid = None
    return line1_copy == line2_copy


def _keep_guids_of_unchanged_lines_stable(
    updated_ahb: FlatAnwendungshandbuch, existing_ahb: FlatAnwendungshandbuch
) -> None:
    """
    Modifies the instance of updated_ahb such that the guids of all lines that are unchanged are the same as in the
    existing_ahb. Only applies if metadata of both AHBs match.
    """
    if updated_ahb.meta == existing_ahb.meta:
        existing_ahb_search_start_index = 0
        for update_index, updated_line in enumerate(updated_ahb.lines.copy()):
            if existing_line_match := first_true(  # ⚠ performance wise this goes like O(n^2)
                existing_ahb.lines[existing_ahb_search_start_index:],
                pred=lambda x: _lines_are_equal_when_ignoring_guid(
                    x, updated_line  # pylint:disable=cell-var-from-loop
                ),
            ):
                updated_ahb.lines[update_index].guid = existing_line_match.guid
                # if we found a line match, we can start the next search at the next line in the next loop iteration
                existing_ahb_search_start_index = existing_ahb.lines.index(existing_line_match) + 1


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
                        bedingung_ausdruck=ahb_expression or None,
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
                        bedingung_ausdruck=row[pruefi] or None,
                        bedingung=row["Bedingung"],
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
                        bedingung_ausdruck=row[pruefi] or None,
                        bedingung=row["Bedingung"],
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
                        bedingung_ausdruck=row[pruefi] or None,
                        bedingung=row["Bedingung"],
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
                        bedingung_ausdruck=row[pruefi] or None,
                        bedingung=row["Bedingung"],
                    )
                )
                continue
            if any(unfolded_ahb_lines) and UnfoldedAhb._is_just_value_pool_entry(ahb_row=row):
                unfolded_ahb_lines.append(
                    UnfoldedAhbLine(
                        index=index,
                        segment_name=current_section_name,
                        segment_gruppe=unfolded_ahb_lines[-1].segment_gruppe,
                        segment=unfolded_ahb_lines[-1].segment,
                        datenelement=unfolded_ahb_lines[-1].datenelement,
                        code=row["Codes und Qualifier"],
                        qualifier="",
                        beschreibung=row["Beschreibung"],
                        bedingung_ausdruck=row[pruefi] or None,
                        bedingung=row["Bedingung"],
                    )
                )

        metadata = {"name": "" or None, "communication_direction": "" or None}
        if len(ahb_table.metadata) > 0:
            metadata["name"] = ahb_table.metadata[0].name or None
            metadata["communication_direction"] = ahb_table.metadata[0].communication_direction or None

        return cls(
            unfolded_ahb_lines=unfolded_ahb_lines,
            meta_data=UnfoldedAhbTableMetaData(
                pruefidentifikator=pruefi,
                beschreibung=metadata["name"],
                kommunikation_von=metadata["communication_direction"],
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

    @staticmethod
    def _is_just_value_pool_entry(ahb_row: pd.Series) -> bool:
        """
        Checks if the given AHB row contains only a value pool entry (w/o Segment (group) and data element)
        """
        return (
            (not ahb_row["Segment Gruppe"])
            and (not ahb_row["Segment"])
            and (not ahb_row["Datenelement"])
            and ahb_row["Codes und Qualifier"]
        )

    def convert_to_flat_ahb(self) -> FlatAnwendungshandbuch:
        """
        Converts the unfolded AHB to a flat AHB.
        """
        meta = AhbMetaInformation(
            pruefidentifikator=self.meta_data.pruefidentifikator,
            description=self.meta_data.beschreibung,
            direction=self.meta_data.kommunikation_von,
        )
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
                    ahb_expression=unfolded_ahb_line.bedingung_ausdruck,
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
        flat_ahb = self.convert_to_flat_ahb()

        file_path = flatahb_output_directory_path / f"{self.meta_data.pruefidentifikator}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as file:
                existing_flat_ahb = FlatAnwendungshandbuchSchema().load(json.load(file))
            _keep_guids_of_unchanged_lines_stable(flat_ahb, existing_flat_ahb)
        dump_data = FlatAnwendungshandbuchSchema().dump(flat_ahb)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(dump_data, file, ensure_ascii=False, indent=2, sort_keys=True)
        logger.info(
            "The flatahb file for %s is saved at %s",
            self.meta_data.pruefidentifikator,
            flatahb_output_directory_path / f"{self.meta_data.pruefidentifikator}.json",
        )
        del flat_ahb
        del dump_data
        if "existing_flat_ahb" in locals():
            del existing_flat_ahb

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
                "Bedingungsausdruck": unfolded_ahb_line.bedingung_ausdruck,
                "Bedingung": unfolded_ahb_line.bedingung,
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
        del df

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

    def collect_condition(self, already_known_conditions: dict) -> None:
        """
        Collect conditions of UnfoldedAHB in dict if they are not known yet.
        """
        df = self.convert_to_dataframe()

        edifact_format = get_format_of_pruefidentifikator(self.meta_data.pruefidentifikator)
        if edifact_format is None:
            logger.warning("'%s' is not a pruefidentifikator", self.meta_data.pruefidentifikator)
            return
        if already_known_conditions.get(edifact_format) is None:
            already_known_conditions[edifact_format] = {}
        # check if there are conditions:
        there_are_conditions = (df["Bedingung"] != "").any()
        if there_are_conditions:
            for conditions_text in df["Bedingung"][df["Bedingung"] != ""]:
                # Split the input into parts enclosed in square brackets and other parts
                matches = re.findall(
                    r"\[(\d+)](.*?)(?=\[\d+]|$)",
                    conditions_text,
                    re.DOTALL,
                )
                for match in matches:
                    # make text prettier:
                    text = match[1].strip()
                    text = re.sub(r"\s+", " ", text)
                    # check whether condition was already collected:
                    condition_key_not_collected_yet = already_known_conditions[edifact_format].get(match[0]) is None
                    if not condition_key_not_collected_yet:
                        key_exits_but_shorter_text = len(text) > len(
                            already_known_conditions[edifact_format].get(match[0])
                        )
                    if condition_key_not_collected_yet or key_exits_but_shorter_text:
                        already_known_conditions[edifact_format][match[0]] = text

        logger.info("The conditions for %s were collected", self.meta_data.pruefidentifikator)
        del df
