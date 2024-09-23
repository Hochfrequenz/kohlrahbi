"""
This module contains the UnfoldedAhbTable class.
"""

import copy
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4

import pandas as pd
from efoli import EdifactFormat, get_format_of_pruefidentifikator
from more_itertools import first_true, peekable
from pydantic import BaseModel

from kohlrahbi.ahbtable.ahbtable import AhbTable, _column_letter_width_mapping
from kohlrahbi.logger import logger
from kohlrahbi.models.anwendungshandbuch import AhbLine, AhbMetaInformation, FlatAnwendungshandbuch
from kohlrahbi.models.flat_ahb_reader import FlatAhbCsvReader
from kohlrahbi.unfoldedahb.unfoldedahbline import UnfoldedAhbLine
from kohlrahbi.unfoldedahb.unfoldedahbtablemetadata import UnfoldedAhbTableMetaData

_segment_group_pattern = re.compile(r"^SG\d+$")
_segment_id_pattern = re.compile(r"^\d{5}$")


def _lines_are_equal_when_ignoring_guid(line1: AhbLine, line2: AhbLine) -> bool:
    """
    returns true iff the line1 and line2 are equal except for their guid
    """
    line1_copy = copy.deepcopy(line1)
    line2_copy = copy.deepcopy(line2)
    line1_copy.guid = None
    line2_copy.guid = None
    return line1_copy == line2_copy


@lru_cache
def _split_data_element_and_segment_id(value: str | None) -> tuple[str | None, str | None]:
    """
    returns the data element id and segment id
    """
    if not value:  # covers both None and empty string
        return None, None
    datenelement_id: str | None
    segment_id: str | None
    if _segment_id_pattern.match(value):
        datenelement_id = None
        segment_id = value
    else:
        datenelement_id = value
        segment_id = None
    return datenelement_id, segment_id


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


class UnfoldedAhb(BaseModel):
    """
    The UnfoldedAhb contains one Prüfidentifikator.
    Some columns in the AHB documents contain multiple information in one column e.g. Segmentname and Segmentgruppe.
    The unfolded classes add new columns/attributes to avoid the duplication of information in one column.
    """

    meta_data: UnfoldedAhbTableMetaData
    unfolded_ahb_lines: list[UnfoldedAhbLine]

    # pylint: disable=too-many-locals
    @classmethod
    def from_ahb_table(cls, ahb_table: AhbTable, pruefi: str) -> "UnfoldedAhb":
        """
        This function creates an UnfoldedAhb from an AhbTable.
        """
        unfolded_ahb_lines: list[UnfoldedAhbLine] = []
        current_section_name: str = ""
        current_segment_id: Optional[str] = None
        # we need to peek one iteration in front of us
        iterable_ahb_table = peekable(ahb_table.table.iterrows())

        for index, series in enumerate(iterable_ahb_table):
            row = series[1]

            current_section_name = UnfoldedAhb._get_section_name(
                segment_gruppe_or_section_name=row["Segment Gruppe"], last_section_name=current_section_name
            )

            if UnfoldedAhb._is_section_name(ahb_row=row):
                current_segment_id = None
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
                        segment_id=current_segment_id,
                    )
                )

            if UnfoldedAhb._is_segment_opening_line(ahb_row=row):
                current_segment_id = row["Segment ID"] or None
                unfolded_ahb_lines.append(
                    UnfoldedAhbLine(
                        index=index,
                        segment_name=current_section_name,
                        segment_gruppe=row["Segment Gruppe"] or None,
                        segment=row["Segment"] or None,
                        datenelement=None,
                        code=None,
                        qualifier="",
                        beschreibung=None,
                        bedingung_ausdruck=row[pruefi] or None,
                        bedingung=row["Bedingung"],
                        segment_id=current_segment_id,
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
                        datenelement=_split_data_element_and_segment_id(row["Datenelement"])[0],
                        segment_id=current_segment_id,
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
                        segment_id=current_segment_id,
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
    def _is_section_name(ahb_row: pd.Series) -> bool:  # type:ignore[type-arg]
        """
        Checks if the current AHB row is a section name.
        It uses the same logic as the function 'line_contains_only_segment_gruppe'
        So to avoid duplicate code, this function just calls the other function.
        """
        return AhbTable.line_contains_only_segment_gruppe(ahb_row)

    @staticmethod
    def _is_segment_group(ahb_row: pd.Series) -> bool:  # type:ignore[type-arg]
        """Checks if the current AHB row is a segment group."""

        if _segment_group_pattern.match(ahb_row["Segment Gruppe"]) and not ahb_row["Segment"]:
            return True
        return False

    @staticmethod
    def _is_segment_opening_line(ahb_row: pd.Series) -> bool:  # type:ignore[type-arg]
        """Checks if the current AHB row is a segment opening line.
        Example:

        SG3    CTA                                         Muss    Muss    Muss
        SG3    CTA    3139    IC    Informationskontakt    X       X       X

        The first line in the example is a segment opening line
        """

        if ahb_row["Segment"] and not ahb_row["Datenelement"]:
            return True
        return False

    @staticmethod
    def _is_just_segment(ahb_row: pd.Series) -> bool:  # type:ignore[type-arg]
        """
        Checks if the given AHB row is a segment
        """

        if (
            _segment_group_pattern.match(ahb_row["Segment Gruppe"])
            and ahb_row["Segment"]
            and not ahb_row["Datenelement"]
        ):
            return True
        if ahb_row["Datenelement"] is not None and _segment_id_pattern.match(ahb_row["Datenelement"]):
            return True
        return False

    @staticmethod
    def _is_dataelement(ahb_row: pd.Series) -> bool:  # type:ignore[type-arg]
        """
        Checks if the given AHB row is a dataelement
        """
        if ahb_row["Datenelement"]:
            return True
        return False

    @staticmethod
    def _is_just_value_pool_entry(ahb_row: pd.Series) -> bool:  # type:ignore[type-arg]
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
            if _line_is_flatahb_line(unfolded_ahb_line):
                lines.append(
                    AhbLine(
                        guid=uuid4(),
                        segment_group_key=unfolded_ahb_line.segment_gruppe,
                        segment_code=unfolded_ahb_line.segment,
                        data_element=unfolded_ahb_line.datenelement,
                        segment_id=unfolded_ahb_line.segment_id,
                        value_pool_entry=unfolded_ahb_line.code,
                        name=unfolded_ahb_line.beschreibung or unfolded_ahb_line.qualifier,
                        ahb_expression=unfolded_ahb_line.bedingung_ausdruck,
                        conditions=unfolded_ahb_line.bedingung,
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

    def get_flatahb_json_file_path(self, output_directory_path: Path) -> Path:
        """
        returns the filepath to where the flat ahb json will be dumped when using dump_flatahb_json()
        raises a value error when the pruefidentifikator is not a valid one
        """
        edifact_format = self._get_format()
        flatahb_output_directory_path = output_directory_path / str(edifact_format) / "flatahb"
        file_path = flatahb_output_directory_path / f"{self.meta_data.pruefidentifikator}.json"
        return file_path

    def dump_flatahb_json(self, output_directory_path: Path) -> None:
        """
        Converts the unfolded AHB to a flat AHB and writes it to a json file.
        The file will be stored in the directory:
            'output_directory_path/<edifact_format>/flatahb/<pruefidentifikator>.json'
        """
        try:
            file_path = self.get_flatahb_json_file_path(output_directory_path)
        except ValueError:
            return
        flatahb_directory = file_path.parent
        flatahb_directory.mkdir(parents=True, exist_ok=True)
        flat_ahb = self.convert_to_flat_ahb()
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = file.read()
                existing_flat_ahb = FlatAnwendungshandbuch.model_validate_json(file_content)
            _keep_guids_of_unchanged_lines_stable(flat_ahb, existing_flat_ahb)
        json_dict = flat_ahb.model_dump(mode="json")
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(json_dict, file, ensure_ascii=False, indent=2, sort_keys=True)
        logger.info(
            "The flatahb file for %s is saved at %s",
            self.meta_data.pruefidentifikator,
            file_path.absolute(),
        )
        del flat_ahb
        del json_dict
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
                "Segment ID": unfolded_ahb_line.segment_id,
                "Code": unfolded_ahb_line.code,
                "Qualifier": unfolded_ahb_line.qualifier,
                "Beschreibung": unfolded_ahb_line.beschreibung,
                "Bedingungsausdruck": unfolded_ahb_line.bedingung_ausdruck,
                "Bedingung": unfolded_ahb_line.bedingung,
            }
            for unfolded_ahb_line in self.unfolded_ahb_lines
            if _line_is_flatahb_line(unfolded_ahb_line)
        ]

        df = pd.DataFrame(unfolded_ahb_lines)
        df.fillna(value="", inplace=True)
        return df

    def get_csv_file_path(self, output_directory_path: Path) -> Path:
        """
        returns the filepath to where the CSV will be dumped when using dump_csv()
        raises a value error when the pruefidentifikator is not a valid one
        """
        edifact_format = self._get_format()
        csv_output_directory_path = output_directory_path / str(edifact_format) / "csv"
        file_path = csv_output_directory_path / f"{self.meta_data.pruefidentifikator}.csv"
        return file_path

    def dump_csv(self, path_to_output_directory: Path) -> None:
        """
        Dump a UnfoldedAHB table into a csv file.
        The file will be stored in the directory:
            'path_to_output_directory/<edifact_format>/csv/<pruefidentifikator>.csv'
        """
        df = self.convert_to_dataframe()
        try:
            csv_file_path = self.get_csv_file_path(path_to_output_directory)
        except ValueError:
            return
        csv_output_directory_path = csv_file_path.parent
        csv_output_directory_path.mkdir(parents=True, exist_ok=True)

        df.to_csv(csv_file_path, encoding="utf-8")
        logger.info("The csv file for %s is saved at %s", self.meta_data.pruefidentifikator, csv_file_path.absolute())
        del df

    def _get_format(self) -> EdifactFormat:
        """extract the edifact format from the metadata pruefidentifikator"""
        edifact_format = get_format_of_pruefidentifikator(self.meta_data.pruefidentifikator)
        if edifact_format is None:
            logger.warning("'%s' is not a pruefidentifikator", self.meta_data.pruefidentifikator)
            raise ValueError(f"'{self.meta_data.pruefidentifikator}' is not a pruefidentifikator")
        return edifact_format

    def get_xlsx_file_path(self, output_directory_path: Path) -> Path:
        """
        returns the filepath to where the xlsx will be dumped when using dump_xlsx()
        raises a value error when the pruefidentifikator is not a valid one
        """
        edifact_format = self._get_format()
        xlsx_output_directory_path: Path = output_directory_path / str(edifact_format) / "xlsx"
        file_path = xlsx_output_directory_path / f"{self.meta_data.pruefidentifikator}.xlsx"
        return file_path

    def dump_xlsx(self, path_to_output_directory: Path) -> None:
        """
        Dump a AHB table of a given pruefi into an excel file.
        The file will be stored in the directory:
            'path_to_output_directory/<edifact_format>/xlsx/<pruefidentifikator>.xlsx'
        """
        try:
            excel_file_path = self.get_xlsx_file_path(path_to_output_directory)
        except ValueError:
            return
        xlsx_output_directory_path = excel_file_path.parent
        xlsx_output_directory_path.mkdir(parents=True, exist_ok=True)

        df = self.convert_to_dataframe()
        try:
            # https://github.com/PyCQA/pylint/issues/3060
            # pylint: disable=abstract-class-instantiated
            with pd.ExcelWriter(excel_file_path, engine="xlsxwriter") as writer:
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
            logger.error("The Excel file %s is open. Please close this file and try again.", excel_file_path)

        logger.info(
            "The xlsx file for %s is saved at %s",
            self.meta_data.pruefidentifikator,
            excel_file_path.absolute(),
        )


def _line_is_flatahb_line(unfolded_ahb_line: UnfoldedAhbLine) -> bool:
    """
    returns true if the unfolded_ahb_line is a valid line for a flat AHB
    """
    return (
        unfolded_ahb_line.segment is not None or unfolded_ahb_line.segment_gruppe is not None
    ) and unfolded_ahb_line.bedingung_ausdruck is not None


def _get_ahb(ahb_model_or_path: Union[FlatAnwendungshandbuch, UnfoldedAhb, Path]) -> FlatAnwendungshandbuch:
    """
    returns the AHB model
    """
    if isinstance(ahb_model_or_path, FlatAnwendungshandbuch):
        return ahb_model_or_path
    if isinstance(ahb_model_or_path, UnfoldedAhb):
        return ahb_model_or_path.convert_to_flat_ahb()
    if isinstance(ahb_model_or_path, Path):
        with open(ahb_model_or_path, "r", encoding="utf-8") as file:
            file_content = file.read()
            return FlatAnwendungshandbuch.model_validate_json(file_content)
    raise ValueError(
        f"argument must be either a FlatAnwendungshandbuch, UnfoldedAhb or a Path but was {type(ahb_model_or_path)}"
    )


def are_equal_except_for_guids(
    ahb_1: Union[FlatAnwendungshandbuch, UnfoldedAhb, Path],
    ahb_2: Union[FlatAnwendungshandbuch, UnfoldedAhb, Path],
) -> bool:
    """returns true iff both provided AHBs are equal except for/when ignoring their line guids"""
    ahb1 = _get_ahb(ahb_1)
    ahb2 = _get_ahb(ahb_2)
    if ahb1.meta != ahb2.meta:
        return False
    if len(ahb1.lines) != len(ahb2.lines):
        return False
    for line1, line2 in zip(ahb1.lines, ahb2.lines, strict=True):
        if not _lines_are_equal_when_ignoring_guid(line1, line2):
            return False
    return True
