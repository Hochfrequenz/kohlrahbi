import re
from pathlib import Path
from uuid import uuid4

import attrs
import pandas as pd
from maus.edifact import get_format_of_pruefidentifikator
from maus.models.anwendungshandbuch import AhbLine, AhbMetaInformation, FlatAnwendungshandbuch
from maus.reader.flat_ahb_reader import FlatAhbCsvReader
from more_itertools import peekable

from kohlrahbi.dump.flatahb import keys_that_must_no_hold_any_values
from kohlrahbi.logger import logger
from kohlrahbi.newahbtable import NewAhbTable
from kohlrahbi.unfoldedahbline import UnfoldedAhbLine
from kohlrahbi.unfoldedahbtablemetadata import UnfoldedAhbTableMetaData

_segment_group_pattern = re.compile(r"^SG\d+$")


@attrs.define(auto_attribs=True, kw_only=True)
class UnfoldedAhb:
    """
    The UnfoldedAhb contains one Prüfidentifikator.
    Some columns in the AHB documents contain multiple information like Segmentname and Segmentgruppe.
    This class unfolds these columns with multiple information.
    """

    meta_data: UnfoldedAhbTableMetaData
    unfolded_ahb_lines: list[UnfoldedAhbLine] = attrs.field(
        validator=attrs.validators.deep_iterable(member_validator=attrs.validators.instance_of(UnfoldedAhbLine))
    )

    @classmethod
    def from_ahb_table(cls, ahb_table: NewAhbTable, pruefi: str):
        unfolded_ahb_lines: list[UnfoldedAhbLine] = []
        index = 0
        current_section_name: str = ""

        # we need to peek one iteration in front of us
        iterable_ahb_table = peekable(ahb_table.table.iterrows())

        for _, row in iterable_ahb_table:
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
                index = index + 1
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
                index = index + 1
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
                index = index + 1
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
                index = index + 1
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
        """

        for row_key in keys_that_must_no_hold_any_values:
            if ahb_row[row_key]:
                return False
        return True

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
        x = self.convert_to_dataframe()
        meta = AhbMetaInformation(pruefidentifikator="11042")
        lines: list[AhbLine] = []

        for unfolded_ahb_line in self.unfolded_ahb_lines:
            lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=unfolded_ahb_line.segment_gruppe,
                    segment_code=unfolded_ahb_line.segment,
                    data_element=unfolded_ahb_line.datenelement,
                    value_pool_entry=unfolded_ahb_line.code,
                    name=unfolded_ahb_line.beschreibung,
                    ahb_expression=unfolded_ahb_line.bedinung_ausdruck,
                    section_name=unfolded_ahb_line.segment_name,
                    index=unfolded_ahb_line.index,
                )
            )

        return FlatAnwendungshandbuch(meta=meta, lines=lines)

    def convert_to_dataframe(self) -> pd.DataFrame:
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

    def to_csv(self, path_to_output_directory: Path):
        """
        Dump a UnfoldedAHB table into a csv file.
        """
        df = self.convert_to_dataframe()

        edifact_format = get_format_of_pruefidentifikator(self.meta_data.pruefidentifikator)
        if edifact_format is None:
            logger.warning("'%s' is not a pruefidentifikator", self.meta_data.pruefidentifikator)
            return

        csv_output_directory_path = path_to_output_directory / "csv" / str(edifact_format)
        csv_output_directory_path.mkdir(parents=True, exist_ok=True)

        df.to_csv(csv_output_directory_path / f"{self.meta_data.pruefidentifikator}.csv")
        logger.info(
            "The csv file for %s is saved at %s",
            self.meta_data.pruefidentifikator,
            csv_output_directory_path / f"{self.meta_data.pruefidentifikator}.csv",
        )
