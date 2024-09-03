# pylint:disable=too-few-public-methods
"""
This module contains classes that are required to model "Anwendungshandbücher" (AHB). There are two kinds of AHBs:
1. the "flat" AHB is very similar to the flat structure scraped from the official PDF files. It has no deep
structure.
2. the "nested" AHB which contains structural information (e.g. that a segment group is contained in
another segment group)
"""
import re
from typing import Annotated, Callable, Optional, Sequence, Union
from uuid import UUID

from more_itertools import last, split_when
from pydantic import BaseModel, Field, StringConstraints, field_validator

from kohlrahbi.models.edifact_components import (
    DataElementFreeText,
    DataElementValuePool,
    Segment,
    SegmentGroup,
    ValuePoolEntry,
)

_VERSION = "0.3.0"  #: version to be written into the deep ahb


# pylint:disable=too-many-instance-attributes
class AhbLine(BaseModel):
    """
    An AhbLine is a single line inside the machine-readable, flat AHB.
    """

    guid: Optional[UUID] = Field(default=None, description="optional key")
    # because the combination (segment group, segment, data element, name) is not guaranteed to be unique
    # yes, it's actually that bad already
    segment_group_key: Optional[str] = Field(default=None, description="the segment group, e.g. 'SG5'")

    segment_code: Optional[str] = Field(default=None, description="the segment, e.g. 'IDE'")

    data_element: Optional[str] = Field(default=None, description="the data element ID, e.g. '3224'")

    segment_id: Optional[str] = Field(
        default=None,
        description="the 5 digit segment id, e.g. '00003' for Nachrichten Kopfsegment. This is available since FV2410.",
    )

    value_pool_entry: Optional[str] = Field(
        None, description="one of (possible multiple) allowed values, e.g. 'E01' or '293'"
    )

    name: Optional[str] = Field(
        None, description="the name, e.g. 'Meldepunkt'. It can be both the description of a field but also its meaning"
    )

    # Check the unittest test_csv_file_reading_11042 to see the different values of name. It's not only the grey fields
    # where user input is expected but also the meanings / values of value pool entries. This means the exact meaning of
    # name can only be determined in the context in which it is used. This is one of many shortcoming of the current AHB
    # structure: Things in the same column don't necessarily mean the same thing.
    ahb_expression: Annotated[Optional[str], StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        default=None,
        description=(
            "a requirement indicator + an optional condition ('ahb expression'),"
            "e.g. 'Muss [123] O [456]'. Note: to parse expressions from AHBs"
            "consider using AHBicht: https://github.com/Hochfrequenz/ahbicht/"
        ),
    )
    conditions: Optional[str] = Field(
        default=None,
        description=(
            "The condition text describes the text to the optional condition of the ahb expression."
            "E.g. '[492] This is a condition text. [999] And this is another one.'"
        ),
    )

    section_name: Optional[str] = Field(
        default=None,
        description=(
            "The section name describes the purpose of a segment,"
            "e.g. 'Nachrichten-Kopfsegment' or 'Beginn der Nachricht'"
        ),
    )

    index: Optional[int] = Field(
        default=None,
        description=(
            "index is a number that describes the position of the AHBLine"
            "inside the original PDF- and FlatAnwendungshandbuch."
        ),
        ge=0,
    )

    def holds_any_information(self) -> bool:
        """
        Returns true iff the line holds any information exception for just a GUID.
        This is useful to filter out empty lines which are artefacts remaining from the scraping process.
        """
        # https://stackoverflow.com/questions/47972143/using-attr-with-pylint
        # pylint: disable=no-member
        return (
            (self.segment_group_key is not None and len(self.segment_group_key.strip()) > 0)
            or (self.segment_code is not None and len(self.segment_code.strip()) > 0)
            or (self.data_element is not None and len(self.data_element.strip()) > 0)
            or (self.value_pool_entry is not None and len(self.value_pool_entry.strip()) > 0)
            or (self.name is not None and len(self.name.strip()) > 0)
            or (self.ahb_expression is not None and len(self.ahb_expression.strip()) > 0)
        )

    def get_discriminator(self, include_name: bool = True) -> str:
        """
        Generate a unique yet readable discriminator for this given line.
        This discriminator is generated just from the line itself without any information on where it occurs.
        It does neither know its position inside the AHB nor parent or sub groups.
        """
        result: str
        if self.segment_group_key:
            result = f"{self.segment_group_key}->"
        else:
            result = ""
        result += f"{self.segment_code}->{self.data_element}"
        if self.name and include_name:
            result += f" ({self.name})"
        return result


class AhbMetaInformation(BaseModel):
    """
    Meta information about an AHB like e.g. its title, Prüfidentifikator, possible sender and receiver roles
    """

    pruefidentifikator: str = Field(
        ..., description="identifies the message type (within a fixed format version) e.g. '11042' or '13012'"
    )
    maus_version: Optional[str] = Field(
        default=_VERSION, description="semantic version of maus used to create this document"
    )
    description: Annotated[Optional[str], StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        default=None,
        description="an optional description of the purpose of the pruefidentifikator; e.g. 'Anmeldung MSB' for 11042",
    )
    direction: Annotated[Optional[str], StringConstraints(strip_whitespace=True, min_length=1)] = Field(
        default=None,
        description=(
            "a stringly typed description of the roles of sender and receiver of the message"
            "(the row name in the AHB is 'Kommunikation von'); e.g. 'MSB an NB' for 11042"
        ),
    )


def _remove_grouped_ahb_lines_containing_section_name(
    grouped_ahb_lines: list[list[AhbLine]], section_name: str
) -> list[list[AhbLine]]:
    """
    Removes all groups of ahb lines that contain a line with the given section name and returns a new list instance.
    """
    return [goal for goal in grouped_ahb_lines if any(ahbl.section_name == section_name for ahbl in goal)]


# pylint:disable=unused-argument
def _check_that_nearly_all_lines_have_a_segment_group(  # type:ignore[no-untyped-def]
    value: list[AhbLine],
):
    """
    Loops over all provided ahb lines and checks that only at the beginning and the end there are lines without a
    segment group. In between every line has to have a segment group specified. This is necessary for the navigation
    to work because it primarily focuses and relies on correct SG information in the lines .
    """
    switches_from_no_sg_to_sg = list(
        split_when(value, lambda x, y: x.segment_group_key is None and y.segment_group_key is not None)
    )
    switches_from_no_sg_to_sg = _remove_grouped_ahb_lines_containing_section_name(
        grouped_ahb_lines=switches_from_no_sg_to_sg, section_name="Abschnitts-Kontrollsegment"
    )
    if len(switches_from_no_sg_to_sg) > 2:
        raise ValueError(f"There is a None segment group in line {last(switches_from_no_sg_to_sg[1])}")


_data_element_pattern = re.compile(r"^\d{4}$|^\d{5}$|^[A-Za-z]+\d{4}$")


# pylint:disable=unused-argument
def _check_that_line_has_either_none_or_d4_data_element(  # type:ignore[no-untyped-def]
    value: AhbLine,
):
    """
    checks that the given line has either a None data element or a data element that matches
    \\d{4},\\ d{5} or [A-Za-z]+\\d{4}.
    AhbLine(data_element = 0001), AhbLine(data_element = 00001) or AhbLine(data_element = R0001)
    """
    if value.data_element is None:
        return
    match = _data_element_pattern.match(value.data_element)
    if match is None:
        raise ValueError(f"The data_element '{value.data_element}' does not match {_data_element_pattern}")


_segment_group_key_pattern = re.compile(r"^SG\d+$")


# pylint:disable=unused-argument
def _check_that_line_has_either_none_or_matching_sg(value: AhbLine):  # type:ignore[no-untyped-def]
    """
    checks that the given line has a segment group key that is either None (for root) or matches SG\\d+
    """
    if value.segment_group_key is None:
        return
    match = _segment_group_key_pattern.match(value.segment_group_key)
    if match is None:
        raise ValueError(
            f"The segment_group_key '{value.segment_group_key}' does not match {_segment_group_key_pattern}"
        )


_segment_code_pattern = re.compile(r"^[A-Z]+$")


# pylint:disable=unused-argument
def _check_that_line_has_either_none_az_segment_code(  # type:ignore[no-untyped-def]
    value: AhbLine,
):
    """
    checks that the given line has either a None segment code or a segment code that consists of all upper letters
    """
    if value.segment_code is None:
        return
    match = _segment_code_pattern.match(value.segment_code)
    if match is None:
        raise ValueError(f"The segment_code '{value.segment_code}' does not match {_segment_code_pattern}")


class FlatAnwendungshandbuch(BaseModel):
    """
    A flat Anwendungshandbuch (AHB) models an Anwendungshandbuch as combination of some meta data and an ordered list
    of `.class:`.FlatAhbLine s. Basically a flat Anwendungshandbuch is the result of a simple scraping approach.
    You can create instances of this class without knowing anything about the "under the hood" structure of AHBs or MIGs
    """

    meta: AhbMetaInformation = Field(..., description="information about this AHB")

    lines: list[AhbLine] = Field(..., description="ordered list lines as they occur in the AHB")

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, value: list[AhbLine]) -> list[AhbLine]:
        """
        The following checks are not baked into the AhbLine class itself, because they might be initialized
        with raw data that do not yet obey these strict validations. But as soon as we bundle them in a
        FlatAnwendungshandbuch, the sanitization shall be applied.
        """
        if value:
            _check_that_nearly_all_lines_have_a_segment_group(value)

        for ahb_line in value:
            _check_that_line_has_either_none_or_d4_data_element(ahb_line)
            _check_that_line_has_either_none_or_matching_sg(ahb_line)
            _check_that_line_has_either_none_az_segment_code(ahb_line)
        return value

    def get_segment_groups(self) -> list[Optional[str]]:
        """
        :return: a set with all segment groups in this AHB in the order in which they occur
        """
        return FlatAnwendungshandbuch._get_available_segment_groups(self.lines)

    @staticmethod
    def _get_available_segment_groups(lines: list[AhbLine]) -> list[Optional[str]]:
        """
        extracts the distinct segment groups from a list of ahb lines
        :param lines:
        :return: distinct segment groups, including None in the order in which they occur
        """
        result: list[Optional[str]] = []
        for line in lines:
            if line.segment_group_key not in result:
                # an "in" check against a set would be faster but we want to preserve both order and readability
                result.append(line.segment_group_key)
        return result

    def sort_lines_by_segment_groups(self):  # type:ignore[no-untyped-def]
        """
        sorts lines by segment groups while preserving the order inside the groups and the order between the groups.
        """
        self.lines = FlatAnwendungshandbuch._sorted_lines_by_segment_groups(self.lines, self.get_segment_groups())

    @staticmethod
    def _sorted_lines_by_segment_groups(ahb_lines: Sequence[AhbLine], sg_order: list[Optional[str]]) -> list[AhbLine]:
        """
        Calls sorted(...) on the provided list and returns a new list.
        Its purpose is, that if a segment group in the AHB (read from top to bottom in the flat ahb/pdf) is interrupted
        by other segment groups, the lines belonging to the same group will be next to each other.
        This is useful to later use a groupby aggregation that only returns one group key per segment group.

        The sort is stable such that the existing order inside the segment groups is maintained.

        Note that this also means, that the order of the return lines no longer the same as in the flat AHB.

        If you provide this function a list:
        [
            (SG2, Foo),
            (SG2, Bar),
            (SG3, ABC),
            (SG3, DEF),
            (SG2, SomethingElse)
        ]
        The result will be:
        [
            (SG2, Foo),
            (SG2, Bar),
            (SG2, SomethingElse)
            (SG3, ABC),
            (SG3, DEF)
        ]

        See the unittests for details.
        """

        # this code is in a static method to make it easily accessible for fine-grained unit testing
        result: list[AhbLine] = sorted(ahb_lines, key=lambda x: x.segment_group_key or "")
        result.sort(key=lambda ahb_line: sg_order.index(ahb_line.segment_group_key))
        return result


class DeepAhbInputReplacement(BaseModel):
    """
    A container class that models replacements of inputs in the DeepAnwendungshandbuch
    """

    #: true iff a replacement is applicable
    replacement_found: bool = Field(..., description="True iff a replacement is applicable")

    # replacements for DataElementValuePool
    value_pool_replacement: Optional[ValuePoolEntry] = Field(
        default=None,
        description=(
            "The replacement for a value pool entry."
            "Note that the replacements may be None even if replacements are found."
        ),
    )
    # replacements for DataElementFreeText
    free_text_replacement: Optional[DataElementFreeText] = Field(
        default=None,
        description=(
            "The replacement for a DataElementFreeText."
            "Note that the replacements may be None even if replacements are found."
        ),
    )


class DeepAnwendungshandbuch(BaseModel):
    """
    The data of the AHB nested as described in the MIG.
    """

    meta: AhbMetaInformation = Field(..., description="Information about this AHB")

    lines: list[SegmentGroup] = Field(..., description="The nested data")

    def reset_ahb_line_index(self) -> None:
        """
        reset the ahb line index for all lines in the DeepAnwendungshandbuch
        :return: nothing; modifies the instance
        """
        for line in self.lines:
            line.reset_ahb_line_index()

    @staticmethod
    def _query_segment_group(
        segment_group: SegmentGroup, predicate: Callable[[SegmentGroup], bool]
    ) -> list[SegmentGroup]:
        """
        recursively search for a segment group that matches the predicate
        :return: return empty list if nothing was found, the matching segment groups otherwise
        """
        result: list[SegmentGroup] = []
        if predicate(segment_group):
            result.append(segment_group)
        if segment_group.segment_groups is not None:
            for sub_group in segment_group.segment_groups:
                sub_result = DeepAnwendungshandbuch._query_segment_group(sub_group, predicate)
                result += sub_result
        return result

    def find_segment_groups(self, predicate: Callable[[SegmentGroup], bool]) -> list[SegmentGroup]:
        """
        recursively search for segment group in this ahb that meets the predicate.
        :return: list of segment groups that match the predicate; empty list otherwise
        """
        result: list[SegmentGroup] = []
        for line in self.lines:
            if line.segment_groups is not None:
                for segment_group in line.segment_groups:
                    result += DeepAnwendungshandbuch._query_segment_group(segment_group, predicate)
            for line_result in DeepAnwendungshandbuch._query_segment_group(line, predicate):
                if line_result not in result:
                    result.append(line_result)
        return result

    def find_segments(
        self,
        group_predicate: Callable[[SegmentGroup], bool] = lambda _: True,
        segment_predicate: Callable[[Segment], bool] = lambda _: True,
    ) -> list[Segment]:
        """
        recursively search for segment characterized by the segment_predicate inside a group characterized by the
        group_predicate.
        :return: list of matching segments, empty list if nothing was found
        """
        result: list[Segment] = []
        for segment_group in self.find_segment_groups(group_predicate):
            result += segment_group.find_segments(segment_predicate)
        for line in self.lines:
            if line.segments is not None:
                for segment in line.segments:
                    if segment_predicate(segment):
                        result.append(segment)
        return result

    def replace_inputs_based_on_discriminator(self, replacement_func: Callable[[str], DeepAhbInputReplacement]) -> None:
        """
        Replace all the entered_inputs in the entire DeepAnwendungshandbuch using the given replacement_func.
        Note that this modifies this DeepAnwendungshandbuch instance (self).
        """
        _replace_inputs_based_on_discriminator(self.lines, replacement_func)

    def get_all_value_pools(self) -> list[DataElementValuePool]:
        """
        recursively find all value pools in the deep ahb
        :return: a list of all value pools
        """
        result: list[DataElementValuePool] = []
        added_discriminators: set[Optional[str]] = set()
        # checks like "str in set" are way faster than "value pool in list"

        def add_to_result(value_pool: DataElementValuePool):  # type:ignore[no-untyped-def]
            if value_pool.discriminator in added_discriminators:
                # assumption: the discriminator is truly unique in an AHB
                return
            if value_pool not in result:
                added_discriminators.add(value_pool.discriminator)
                result.append(value_pool)

        for segment in self.find_segments():
            for sub_result in segment.get_all_value_pools():
                add_to_result(sub_result)
        for segment_group in self.find_segment_groups(lambda _: True):
            for sub_result in segment_group.get_all_value_pools():
                add_to_result(sub_result)
        return list(result)

    def get_all_expressions(self) -> list[str]:
        """
        recursively iterate through the deep ahb and return all distinct expressions found
        """
        result: set[str] = set()
        for segment in self.find_segments():
            if segment.ahb_expression:
                result.add(segment.ahb_expression)
            for data_element in segment.data_elements:
                if isinstance(data_element, DataElementFreeText):
                    if data_element.ahb_expression:
                        result.add(data_element.ahb_expression)
                elif isinstance(data_element, DataElementValuePool):
                    for value_pool_entry in data_element.value_pool:
                        if value_pool_entry.ahb_expression:
                            result.add(value_pool_entry.ahb_expression)
        for segment_group in self.find_segment_groups(lambda _: True):
            if segment_group.ahb_expression:
                result.add(segment_group.ahb_expression)
        return sorted(result)


def _replace_inputs_based_on_discriminator(
    segment_groups: list[SegmentGroup], replacement_func: Callable[[str], DeepAhbInputReplacement]
) -> None:
    """
    Replace all the entered_inputs in the entire list of segment groups using the given replacement_func.
    """

    def process_data_element(
        data_element: Union[DataElementFreeText, DataElementValuePool], replacement_result: DeepAhbInputReplacement
    ) -> None:
        if isinstance(data_element, DataElementFreeText) and replacement_result.free_text_replacement:
            data_element.free_text = replacement_result.free_text_replacement.free_text
        elif isinstance(data_element, DataElementValuePool) and replacement_result.value_pool_replacement:
            data_element.value_pool.append(replacement_result.value_pool_replacement)

    def process_segment(segment: Segment) -> None:
        for data_element in segment.data_elements:
            if data_element.discriminator:
                replacement_result = replacement_func(data_element.discriminator)
                if replacement_result.replacement_found:
                    process_data_element(data_element, replacement_result)

    for segment_group in segment_groups:
        if segment_group.segment_groups:
            _replace_inputs_based_on_discriminator(segment_group.segment_groups, replacement_func)

        if segment_group.segments:
            for segment in segment_group.segments:
                process_segment(segment)
