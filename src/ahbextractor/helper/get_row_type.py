"""
This module contains all functions to define the type of a row of the tables in an AHB.
"""

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import _Cell  # type:ignore[import]

from ahbextractor.enums import RowType, RowTypeColor
from ahbextractor.helper.row_type_checker import (
    is_row_datenelement,
    is_row_empty,
    is_row_header,
    is_row_segment,
    is_row_segmentgruppe,
    is_row_segmentname,
)


def set_table_header_bg_color(cell, hex_color: str):
    """
    set background shading for Header Rows
    """
    tblCell = cell._tc
    tblCellProperties = tblCell.get_or_add_tcPr()
    clShading = OxmlElement("w:shd")
    clShading.set(qn("w:fill"), hex_color)  # Hex of Dark Blue Shade {R:0x00, G:0x51, B:0x9E}
    tblCellProperties.append(clShading)
    return cell


def get_row_type(edifact_struktur_cell: _Cell, left_indent_position: int) -> RowType:
    """Defines the type of the current row.

    Args:
        edifact_struktur_cell (_Cell): Indicator cell
        left_indent_position (int): Position of the left indent

    Raises:
        NotImplemented: Gets raised if the RowType got not to be defined

    Returns:
        RowType: Type of the current row
    """
    if is_row_header(edifact_struktur_cell=edifact_struktur_cell):
        # edifact_struktur_cell.
        set_table_header_bg_color(edifact_struktur_cell, RowTypeColor.HEADER)
        return RowType.HEADER

    if is_row_segmentname(edifact_struktur_cell=edifact_struktur_cell):
        set_table_header_bg_color(edifact_struktur_cell, RowTypeColor.SEGMENTNAME)
        return RowType.SEGMENTNAME

    if is_row_segmentgruppe(edifact_struktur_cell=edifact_struktur_cell, left_indent_position=left_indent_position):
        set_table_header_bg_color(edifact_struktur_cell, RowTypeColor.SEGMENTGRUPPE)
        return RowType.SEGMENTGRUPPE

    if is_row_segment(edifact_struktur_cell=edifact_struktur_cell, left_indent_position=left_indent_position):
        set_table_header_bg_color(edifact_struktur_cell, RowTypeColor.SEGMENT)
        return RowType.SEGMENT

    if is_row_datenelement(edifact_struktur_cell=edifact_struktur_cell, left_indent_position=left_indent_position):
        set_table_header_bg_color(edifact_struktur_cell, RowTypeColor.DATENELEMENT)
        return RowType.DATENELEMENT

    if is_row_empty(edifact_struktur_cell=edifact_struktur_cell):
        set_table_header_bg_color(edifact_struktur_cell, RowTypeColor.EMPTY)
        return RowType.EMPTY

    raise NotImplementedError(f"Could not define row type of cell with text: {edifact_struktur_cell.text}")
