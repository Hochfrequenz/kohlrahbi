"""
This module contains the TableHeader class.
"""

from enum import StrEnum
from typing import Dict, List, Optional

from attrs import define
from docx.table import _Cell  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]


class HeaderSection(StrEnum):
    """
    Enum for the different sections of the table header
    """

    BESCHREIBUNG = "beschreibung"
    KOMMUNIKATION = "kommunikation"
    PRUEFIDENTIFIKATOR = "pruefidentifikator"


def get_tabstop_positions(paragraph: Paragraph) -> List[int]:
    """Find all tabstop positions in a given paragraph.

    Mainly the tabstop positions of cells from the middle column are determined

    Args:
        paragraph (Paragraph):

    Returns:
        List[int]: All tabstop positions in the given paragraph
    """
    tabstop_positions: List[int] = []
    for tabstop in paragraph.paragraph_format.tab_stops:
        tabstop_positions.append(tabstop.position)
    return tabstop_positions


def get_tabstop_postions_of_pruefis(tabstop_positions: List[int]) -> List[int]:
    """
    Get the tabstop positions of the Prüfidentifikatoren columns.
    The first and the last tabstop position are not part of the Prüfidentifikatoren columns.

    """

    return tabstop_positions[1:-1]


def create_mapping_of_tabstop_positions(
    initial_tabstop_positions: List[int],
    current_tabstop_positions: List[int],
) -> Dict[int, int]:
    """
    Create a mapping of the tabstop positions of the Prüfidentifikatoren columns.
    """
    # create a mapping of the tabstop positions
    mapping: Dict[int, int] = {}
    # Sort the lists in ascending order
    initial_tabstop_positions.sort()
    current_tabstop_positions.sort()

    # Iterate over the sorted lists and find the entries with the least difference
    for i, current_pos in enumerate(current_tabstop_positions):
        min_diff = float("inf")
        min_j = None
        for j, initial_pos in enumerate(initial_tabstop_positions):
            diff = abs(current_pos - initial_pos)
            if diff < min_diff:
                min_diff = diff
                min_j = j
        if min_j is None:
            raise ValueError("min_j should not be None")

        mapping[current_tabstop_positions[i]] = initial_tabstop_positions[min_j]

    return mapping


@define
class PruefiMetaData:
    """
    This class contains the information about the Prüfidentifikatoren
    """

    pruefidentifikator: str
    name: str
    communication_direction: str


@define
class TableHeader:
    """
    Class for the table header.
    It contains the information about the Prüfidentifikatoren.
    """

    pruefi_meta_data: List[PruefiMetaData] = []

    @classmethod
    def from_header_cell(cls, row_cell: _Cell) -> "TableHeader":
        """
        Create a TableHeader instance from a list of strings
        """

        def initialize_collector(paragraph) -> Dict[str, Dict[str, str | int]]:
            """
            Initialize the collector dictionary.
            The collector dictionary contains the information about the Prüfidentifikatoren.
            """
            current_tabstop_positions = get_tabstop_positions(paragraph=paragraph)
            splitted_text = paragraph.text.split("\t")
            splitted_text.remove("Prüfidentifikator")

            collector: Dict[str, Dict[str, str | int]] = {}

            for pruefidentifikator, tab_stop in zip(splitted_text, current_tabstop_positions):
                collector[pruefidentifikator] = {
                    HeaderSection.BESCHREIBUNG.value: "",
                    HeaderSection.KOMMUNIKATION.value: "",
                    "tabstop_position": tab_stop,
                }

            if collector == {}:
                raise ValueError("collector should not be empty")

            return collector

        if not row_cell.paragraphs[-1].text.startswith("Prüfidentifikator"):
            raise ValueError("The last paragraph should start with 'Prüfidentifikator'")

        pruefidentifikator_paragraoh = row_cell.paragraphs[-1]

        collector = initialize_collector(paragraph=pruefidentifikator_paragraoh)

        # you need to loop over the paragraphs cause we need the tabstop positions of the paragraphs

        section_type: Optional[HeaderSection] = None

        for paragraph in row_cell.paragraphs:
            if paragraph.text.startswith("Prüfidentifikator"):
                continue
            if paragraph.text.startswith("Beschreibung"):
                initial_tabstop_positions = get_tabstop_positions(paragraph=paragraph)

                section_type = HeaderSection.BESCHREIBUNG

                tabstop_mapper = dict(zip(initial_tabstop_positions, collector.keys()))

                splitted_text = paragraph.text.split("\t")
                splitted_text.remove("Beschreibung")

                for pruefi, text in zip(collector.keys(), splitted_text):
                    collector[pruefi][HeaderSection.BESCHREIBUNG.value] = text + " "

            elif paragraph.text.startswith("Kommunikation"):
                initial_tabstop_positions = get_tabstop_positions(paragraph=paragraph)

                section_type = HeaderSection.KOMMUNIKATION

                collector.keys()

                tabstop_mapper = {
                    tabstop_position: pruefi
                    for tabstop_position, pruefi in zip(initial_tabstop_positions, collector.keys())
                }

                splitted_text = paragraph.text.split("\t")
                splitted_text.remove("Kommunikation von")
                for pruefi, text in zip(collector.keys(), splitted_text):
                    collector[pruefi][HeaderSection.KOMMUNIKATION.value] = text + " "

            else:
                current_tabstop_positions = get_tabstop_positions(paragraph=paragraph)
                splitted_text = paragraph.text.split("\t")
                if "" in splitted_text:
                    splitted_text.remove("")

                for tabstop_position, text in zip(current_tabstop_positions, splitted_text):
                    pruefi = tabstop_mapper[tabstop_position]
                    collector[pruefi][section_type.value] += text + " "

        pruefi_meta_data = []

        def ensure_single_space_between_words(text: str) -> str:
            """
            Ensure that there is only one space between words
            """
            return " ".join(text.split())

        for pruefi, meta_data in collector.items():
            if isinstance(meta_data[HeaderSection.BESCHREIBUNG.value], int) or isinstance(
                meta_data[HeaderSection.KOMMUNIKATION.value], int
            ):
                raise ValueError("The meta data should not be an int")

            pruefi_with_meta_data = PruefiMetaData(
                pruefidentifikator=pruefi,
                communication_direction=ensure_single_space_between_words(meta_data[HeaderSection.KOMMUNIKATION.value]),
                name=ensure_single_space_between_words(meta_data[HeaderSection.BESCHREIBUNG.value]),
            )

            pruefi_meta_data.append(pruefi_with_meta_data)

        return cls(pruefi_meta_data=pruefi_meta_data)

    def get_pruefidentifikatoren(self) -> List[str]:
        """
        Get all Prüfidentifikatoren
        """
        return [pruefi.pruefidentifikator for pruefi in self.pruefi_meta_data]
