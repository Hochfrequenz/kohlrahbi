"""
A module that reads AHBs from a given CSV file
"""

import csv
import logging
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal, Optional, Sequence, TextIO, Tuple, overload

from kohlrahbi.models.anwendungshandbuch import _VERSION, AhbLine, AhbMetaInformation, FlatAnwendungshandbuch
from kohlrahbi.models.edifact_components import gabi_edifact_qualifier_pattern

_pruefi_pattern = re.compile(r"^\d{5}$")  #: five digits
_value_pool_entry_pattern = re.compile(r"^(?!MP-ID)[A-Z0-9\-i]{2,}$")  # i for GABi -- why?
_numeric_value_pool_entry_pattern = re.compile(r"^\d+(?:\.\d+)?[a-z]?$")
_ebd_code_pattern = re.compile(r"^([EG])_\d+$")
_segment_group_pattern = re.compile(r"^SG\d+$")


# pylint:disable=too-few-public-methods
class FlatAhbReader(ABC):
    """
    An AHB Reader reads AHB data from a source and is able to convert them to a :class:`.FlatAnwendungshandbuch`
    """

    @abstractmethod
    def to_flat_ahb(self) -> FlatAnwendungshandbuch:
        """
        convert the read data into a flat anwendungshandbuch
        :return:
        """
        raise NotImplementedError("The inheriting class has to implement this method")


def check_file_can_be_parsed_as_ahb_csv(file_path: Path) -> None:
    """
    Returns nothing iff the given file is parsable as CSV and contains no obvious errors.
    This is not a really sophisticated analysis but just a basic minimal sanity check.
    In case of error an exception is raised.
    """
    _ = FlatAhbCsvReader(file_path)  # this may die with a meaningful exception


class FlatAhbCsvReader(FlatAhbReader):
    """
    reads csv files and returns AHBs
    """

    def __init__(  # type:ignore[no-untyped-def]
        self,
        file_path: Path,
        pruefidentifikator: Optional[str] = None,
        encoding="utf-8",
        delimiter=",",
    ):
        self.rows: list[AhbLine] = []
        self._logger = logging.getLogger()
        self.current_section_name: Optional[str] = None
        self.pruefidentifikator = pruefidentifikator
        self.delimiter = delimiter
        self.bedingungen: dict[str, str] = {}
        with open(file_path, "r", encoding=encoding) as infile:
            # current_section_name: Optional[str]
            raw_lines = self.get_raw_rows(infile)
        raw_lines_with_merged_section_names = FlatAhbCsvReader.merge_section_only_lines(raw_lines)
        for row_index, row in enumerate(raw_lines_with_merged_section_names):
            ahb_line = self.raw_ahb_row_to_ahbline(row)
            if ahb_line is None:
                continue
            ahb_line.index = row_index  # it is ascending but not continuous
            self.rows.append(ahb_line)

    @staticmethod
    def merge_section_only_lines(raw_lines: list[dict]) -> list[dict]:  # type:ignore[type-arg]
        """
        merges adjacent lines from the CSV source when they only contain an AHB "section" description.
        "Section" headings are the grey lines on the left of the AHB PDF.
        (The first section of each AHB is "Nachrichten-Kopfsegment" in most cases.)
        When the section heading spans multiple lines, we don't want to treat them as separate but as a single heading.
        The method consumes a list of dicts and returns a _new_ list of dicts that is of the same length or shorter.
        """
        result: list[dict] = []  # type:ignore[type-arg]

        # imagine the original list to be
        # 0,asd,qwertz,
        # 1,a very long section,
        # 2,heading that spans,
        # 3,multiple lines,
        # 4,Foo,Bar,Y
        # 5,Baz,Boom,Z
        # we then want to merge the lines with index 1-3 into a single line
        keys_that_must_no_hold_any_values: set[str] = {
            "Segment",
            "Datenelement",
            "Codes und Qualifier",
            "Beschreibung",
            "Bedingung",
        }

        def line_only_contains_segment_gruppe(raw_line: dict) -> bool:  # type:ignore[type-arg]
            """
            returns true if the given raw line only contains some meaningful data in the "Segment Gruppe" key
            """
            for row_key in keys_that_must_no_hold_any_values:
                if row_key in raw_line and raw_line[row_key] is not None and len(raw_line[row_key].strip()) > 0:
                    return False
            return True

        merged_section_name = ""
        number_of_lines_merged = 0
        for raw_line in raw_lines:
            if (
                "Segment Gruppe" in raw_line
                and raw_line["Segment Gruppe"]
                and line_only_contains_segment_gruppe(raw_line)
                and not raw_line["Segment Gruppe"].startswith("SG")
            ):
                merged_section_name += " " + raw_line["Segment Gruppe"]
                number_of_lines_merged += 1
            else:
                # note that AHBs never end with a section heading, so all headings/sections will run into this block
                if len(merged_section_name) > 0:
                    artificial_merged_line: dict = {  # type:ignore[type-arg]
                        "": str(int(raw_line[""]) - 1),
                        "Segment Gruppe": merged_section_name.strip().replace("  ", " "),
                    }
                    for key in keys_that_must_no_hold_any_values:
                        # although we know there's no meaningful value here, we still need the keys with empty values
                        # so that to downstream code the line seems legit ➡ We re-add them.
                        artificial_merged_line[key] = ""
                    result.append(artificial_merged_line)
                    merged_section_name = ""
                    number_of_lines_merged = 0
                result.append(raw_line)
        return result

    def get_raw_rows(self, file_handle: TextIO) -> list[dict]:  # type:ignore[type-arg]
        """
        reads the input file and returns an iterator over raw lines.
        Override this method if your data source is not a CSV file
        """
        reader = csv.DictReader(file_handle, delimiter=self.delimiter)
        if not self.pruefidentifikator:
            self.pruefidentifikator = FlatAhbCsvReader._get_name_of_expression_column(reader.fieldnames)
        if not self.pruefidentifikator:
            raise ValueError("Cannot find column name for ahb expression")
        return list(reader)

    def raw_ahb_row_to_ahbline(self, ahb_row: dict) -> Optional[AhbLine]:  # type:ignore[type-arg]
        """
        Converts a row of the raw/scraped AHB into the AhbLine data structure.
        Returns None for rows that are skipped.
        Override this method is your column names/input data structure differs.
        """
        value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
            ahb_row["Codes und Qualifier"], ahb_row["Beschreibung"]
        )
        self.bedingungen.update(FlatAhbCsvReader._extract_bedingungen(ahb_row["Bedingung"]))
        segment_group: Optional[str] = None
        if FlatAhbCsvReader._is_segment_group(ahb_row["Segment Gruppe"]):
            segment_group = ahb_row["Segment Gruppe"]
        elif len(ahb_row["Segment Gruppe"]) >= 3:
            self.current_section_name = ahb_row["Segment Gruppe"].strip() or None  # e.g. "Nachrichten-Kopfsegment"
            self._logger.debug("Processing %s section '%s'", self.pruefidentifikator, self.current_section_name)
            return None  # possibly a section heading like "Nachrichten-Endesegment"
            # this is different from segment group = None which is value for e.g. the UNH
        result: AhbLine = AhbLine(
            guid=uuid.uuid4(),
            segment_group_key=segment_group,
            segment_code=ahb_row["Segment"] or None,
            data_element=ahb_row["Datenelement"] or None,
            value_pool_entry=value_pool_entry,
            ahb_expression=ahb_row[self.pruefidentifikator] or None,
            name=description,
            section_name=_replace_hardcoded_section_names(self.current_section_name),
        )
        return result

    def extract_condition_texts(self) -> dict[str, str]:
        """
        Extracts all the condition texts found in this AHB.
        :return: a dictionary with the condition key (e.g. "46") as value and the condition text (e.g. "Wenn aus Sparte
        Gas") as value. The value does not contain the "[46]" prefix.
        """
        return self.bedingungen

    @staticmethod
    def separate_value_pool_entry_and_name(
        x: Optional[str], y: Optional[str]  # pylint:disable=invalid-name
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        The PDFs are so broken, that sometimes the Codes column contains the description of the line instead of the code
        This function returns a value_pool_entry at index 0, a possible description at index 1, even if they're mixed up
        in the source files.
        """
        if x is not None:
            x = x.strip()
        if y is not None:
            y = y.strip()
        if FlatAhbCsvReader._is_value_pool_entry(x) and not FlatAhbCsvReader._is_value_pool_entry(y):
            return x, y or None
        if FlatAhbCsvReader._is_value_pool_entry(x) and FlatAhbCsvReader._is_value_pool_entry(y):
            # Both look like a value pool entry. This typically happens e.g. for date qualifiers or code lists
            return x, y
        return y or None, x or None

    @staticmethod
    def _is_value_pool_entry(candidate: Optional[str]) -> bool:
        """
        Returns true iff the provided candidate is a possible value pool entry.
        """
        if not candidate:
            return False
        if _value_pool_entry_pattern.match(candidate) is not None:
            return True
        # numbers alone might be value pool entries even if they don't match the regex
        # we don't use "isdigit" because isdigit e.g. does not match '1.2'
        if _numeric_value_pool_entry_pattern.match(candidate) is not None:
            return True
        if len(candidate) == 1 and candidate.upper() == candidate:
            return True
        if gabi_edifact_qualifier_pattern.match(candidate) is not None:
            return True
        return _ebd_code_pattern.match(candidate) is not None

    @staticmethod
    def _is_segment_group(candidate: Optional[str]) -> bool:
        """
        Returns true iff the provided candidate is a possible segment group
        """
        if not candidate:
            return False
        return _value_pool_entry_pattern.match(candidate) is not None

    _bedingung_pattern = re.compile(r"\[(?P<key>\d+)\]\s*(?P<text>[^\[\]]+)\s*")  # https://regex101.com/r/hN5x9w/1

    @staticmethod
    def _extract_bedingungen(candidate: Optional[str]) -> dict[str, str]:
        """
        Checks if the given candidate is a bedingung. If no, returns empty dict.
        If yes returns a dictionary where the Bedingung keys (e.g. "494") are dictionary keys and the Bedingung
        texts (e.g. "Der Wert muss ≤ der zum Erzeugungszeitpunkt sein.") are the dictionary values.
        The result is a dict because often there are multiple conditions connected to a single line in the AHB.
        """
        if not candidate:
            return {}
        return {m[0]: m[1].strip() for m in FlatAhbCsvReader._bedingung_pattern.findall(candidate)}

    @staticmethod
    def _get_name_of_expression_column(field_names: Optional[Sequence[str]]) -> Optional[str]:
        """
        Gets the name of the column that holds the AHB expressions.
        This allows us to read any AHB without a priori knowledge of its pruefidentifikator.

        :param field_names: list of fieldnames
        :return: the first field name that is a 5 digit name or None if none is found.
        """
        if not field_names:
            return None
        for field_name in field_names:
            if _pruefi_pattern.match(field_name):
                return field_name
        return None

    def to_flat_ahb(self) -> FlatAnwendungshandbuch:
        """
        Converts the content of the CSV file to a FlatAnwendungshandbuch.
        :return:
        """
        return FlatAnwendungshandbuch(
            meta=AhbMetaInformation(
                pruefidentifikator=self.pruefidentifikator,  # type:ignore[arg-type]
                maus_version=_VERSION,
            ),
            lines=[row for row in self.rows if row.holds_any_information()],
        )


@overload
def _replace_hardcoded_section_names(section_name: str) -> str: ...


@overload
def _replace_hardcoded_section_names(section_name: Literal[None]) -> Literal[None]: ...


def _replace_hardcoded_section_names(section_name: Optional[str]) -> Optional[str]:
    """
    Replace section names that differ because of "Datenschiefstände"
    :param section_name:
    :return:
    """
    if not section_name:
        return section_name
    replacements: dict[str, str] = {
        # https://github.com/Hochfrequenz/edifact-templates/issues/82
        # pylint: disable=line-too-long
        "OBIS-Kennzahl der Zähleinrichtung / Mengenumwerter / Smartmeter-Gateway": "OBIS-Kennzahl der Zähleinrichtung / Mengenumwerter",
        "OBIS-Daten der Zähleinrichtung / Mengenumwerter / Smartmeter-Gateway": "OBIS-Daten der Zähleinrichtung / Mengenumwerter",
        # https://github.com/Hochfrequenz/edifact-templates/issues/80
        "OBIS Daten für Lieferant relevant": "OBIS Daten für Marktrolle relevant",
    }
    if section_name.strip() in replacements:
        return replacements[section_name]
    return section_name
