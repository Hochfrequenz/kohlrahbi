from enum import Enum
from typing import List


class RowType(Enum):
    SEGMENTNAME = 1
    SEGMENTGRUPPE = 2
    SEGMENT = 3
    DATENELEMENT = 4
    HEADER = 5
    EMPTY = 6


def is_row_header(text_in_row_as_list) -> bool:
    if text_in_row_as_list[0] == "EDIFACT Struktur":
        return True

    return False


def is_row_segmentname(table, text_in_row_as_list: List) -> bool:
    """
    Checks if the actual row contains just the segment name like "Nachrichten-Kopfsegment"
    """

    if text_in_row_as_list[0] and not text_in_row_as_list[1] and not text_in_row_as_list[2]:
        return True

    return False


def is_row_segmentgruppe(edifact_struktur_cell, left_indent_position: int) -> bool:
    if (
        edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == left_indent_position
        and not "\t" in edifact_struktur_cell.text
    ):
        return True

    return False


def is_row_segment(edifact_struktur_cell, left_indent_position: int) -> bool:
    # |   UNH    |
    if (
        not edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == left_indent_position
        and not "\t" in edifact_struktur_cell.text
        and not edifact_struktur_cell.text == ""
    ):
        return True

    # | SG2\tNAD |
    if (
        edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == left_indent_position
        and edifact_struktur_cell.text.count("\t") == 1
    ):
        return True

    return False


def is_row_datenelement(edifact_struktur_cell, left_indent_position: int) -> bool:
    # |   UNH\t0062 |
    if (
        not edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == left_indent_position
        and "\t" in edifact_struktur_cell.text
    ):
        return True

    # | SG2\tNAD\t3035 |
    if (
        edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == left_indent_position
        and edifact_struktur_cell.text.count("\t") == 2
    ):
        return True

    return False


def is_row_empty(edifact_struktur_cell) -> bool:
    if edifact_struktur_cell.text == "":
        return True
    return False


def define_row_type(edifact_struktur_cell, text_in_row_as_list, left_indent_position: int) -> RowType:
    if is_row_header(text_in_row_as_list=text_in_row_as_list):
        return RowType.HEADER

    elif is_row_segmentname(text_in_row_as_list=text_in_row_as_list):
        return RowType.SEGMENTNAME

    elif is_row_segmentgruppe(edifact_struktur_cell=edifact_struktur_cell, left_indent_position=left_indent_position):
        return RowType.SEGMENTGRUPPE

    elif is_row_segment(edifact_struktur_cell=edifact_struktur_cell, left_indent_position=left_indent_position):
        return RowType.SEGMENT

    elif is_row_datenelement(edifact_struktur_cell=edifact_struktur_cell, left_indent_position=left_indent_position):
        return RowType.DATENELEMENT

    elif is_row_empty(edifact_struktur_cell=edifact_struktur_cell):
        return RowType.EMPTY

    else:
        raise NotImplemented(f"Could not define row type of {text_in_row_as_list}")
