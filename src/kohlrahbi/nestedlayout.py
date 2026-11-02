"""
Support for the "nested" AHB table layout which the BDEW uses for documents published since mid 2025.

In the older layout, the middle and the right column of an AHB table contain paragraphs whose contents are aligned
using tab stops (see BodyCell and TableHeader). In the nested layout, the cells of the outer table contain inner
tables instead. Each inner cell holds exactly one value (e.g. a segment, a code or the expression of one
Prüfidentifikator). The empty "spacer" cells between them vary from row to row, so cells are assigned to columns by
their horizontal position (derived from the grid column widths), not by their index.

The parser creates the same dataframe as the parser for the old layout, so that all downstream processing
(sanitizing, csv/xlsx/flatahb export) is shared.
"""

import re
from collections.abc import Generator

import pandas as pd
from docx.oxml.ns import qn
from docx.oxml.table import CT_Row, CT_Tbl, CT_Tc
from docx.oxml.xmlchemy import BaseOxmlElement
from docx.table import Table
from pydantic import BaseModel

from kohlrahbi.docxtablecells.bedinungscell import BedingungCell
from kohlrahbi.logger import logger
from kohlrahbi.table_header import PruefiMetaData

_segment_group_pattern = re.compile(r"^SG\d+$")
_segment_pattern = re.compile(r"^[A-Z]{3}$")
_data_element_pattern = re.compile(r"^\d{4}$")
_segment_id_pattern = re.compile(r"^[A-Z\d]\d{4}$")
_pruefi_pattern = re.compile(r"^\d{5}$")


class PositionedText(BaseModel):
    """
    The text of a single (inner or outer) table cell together with its horizontal extent.
    The position is measured in the units of the grid column widths, relative to the left edge of the outer table.
    """

    text: str
    x_start: int
    x_end: int

    @property
    def x_center(self) -> float:
        """the horizontal center of the cell"""
        return (self.x_start + self.x_end) / 2

    def overlap(self, x_start: int, x_end: int) -> int:
        """the length of the horizontal overlap with the given range"""
        return max(0, min(self.x_end, x_end) - max(self.x_start, x_start))


def is_nested_layout_table(table: Table) -> bool:
    """
    Checks if the given AHB table uses the nested layout, i.e. if the header cell with the Prüfidentifikatoren
    contains an inner table.
    """
    header_cell = table._tbl.tr_lst[0].tc_lst[-1]  # pylint:disable=protected-access
    return len(header_cell.findall(qn("w:tbl"))) > 0


def _is_invisible_run(run: BaseOxmlElement) -> bool:
    """
    The nested layout contains invisible placeholder texts (e.g. '..' in white 4pt font) which are no content.
    """
    run_properties = run.find(qn("w:rPr"))
    if run_properties is None:
        return False
    color = run_properties.find(qn("w:color"))
    is_white = color is not None and color.get(qn("w:val")) == "FFFFFF"
    return is_white or run_properties.find(qn("w:vanish")) is not None


def _cell_text(tc: CT_Tc) -> str:
    """the whitespace normalized, visible text of the paragraphs that are direct children of the cell"""
    paragraph_texts = [
        "".join(t.text or "" for run in p.iter(qn("w:r")) if not _is_invisible_run(run) for t in run.iter(qn("w:t")))
        for p in tc.findall(qn("w:p"))
    ]
    return " ".join(" ".join(paragraph_texts).replace("\xa0", " ").split())


def _get_grid_column_positions(tbl: CT_Tbl, x_offset: int) -> list[int]:
    """the x positions of the left edges of all grid columns (plus the right edge of the last one)"""
    grid_column_positions = [x_offset]
    for grid_column in tbl.tblGrid.gridCol_lst:
        grid_column_positions.append(grid_column_positions[-1] + int(grid_column.w or 0))
    return grid_column_positions


def _iter_row_cells_with_position(
    tr: CT_Row, grid_column_positions: list[int]
) -> Generator[tuple[int, int, CT_Tc], None, None]:
    """yields (x_start, x_end, cell) for all cells of the given table row"""
    last_index = len(grid_column_positions) - 1
    grid_index = tr.grid_before
    for tc in tr.tc_lst:
        x_start = grid_column_positions[min(grid_index, last_index)]
        grid_index += tc.grid_span
        x_end = grid_column_positions[min(grid_index, last_index)]
        yield x_start, x_end, tc


def _iter_cells_with_position(tbl: CT_Tbl, x_offset: int) -> Generator[tuple[int, int, int, CT_Tc], None, None]:
    """
    yields (row index, x_start, x_end, cell) for all cells of the given table.
    The positions are derived from the widths of the grid columns of the table.
    """
    grid_column_positions = _get_grid_column_positions(tbl, x_offset)
    for row_index, tr in enumerate(tbl.tr_lst):
        for x_start, x_end, tc in _iter_row_cells_with_position(tr, grid_column_positions):
            yield row_index, x_start, x_end, tc


def get_lines_of_outer_cell(tc: CT_Tc, x_start: int, x_end: int) -> list[list[PositionedText]]:
    """
    Returns the texts of an outer cell, grouped into lines.
    The direct text of the outer cell is part of the first line, each row of an inner table is a line of its own.
    """
    lines: list[list[PositionedText]] = [[]]
    direct_text = _cell_text(tc)
    if direct_text:
        lines[0].append(PositionedText(text=direct_text, x_start=x_start, x_end=x_end))
    for inner_table in tc.findall(qn("w:tbl")):
        for row_index, inner_x_start, inner_x_end, inner_tc in _iter_cells_with_position(inner_table, x_start):
            while len(lines) <= row_index:
                lines.append([])
            text = _cell_text(inner_tc)
            if text:
                lines[row_index].append(PositionedText(text=text, x_start=inner_x_start, x_end=inner_x_end))
            if inner_tc.findall(qn("w:tbl")):
                raise NotImplementedError("Inner tables of inner tables are not supported")
    return lines


def get_lines_of_outer_row(table: Table, row_index: int) -> list[list[PositionedText]]:
    """
    Returns the texts of all cells of one row of the outer table, grouped into lines.
    The n-th line of the row is the combination of the n-th lines of all outer cells.
    """
    tbl = table._tbl  # pylint:disable=protected-access
    combined_lines: list[list[PositionedText]] = []
    grid_column_positions = _get_grid_column_positions(tbl, 0)
    for x_start, x_end, tc in _iter_row_cells_with_position(tbl.tr_lst[row_index], grid_column_positions):
        for line_index, line in enumerate(get_lines_of_outer_cell(tc, x_start, x_end)):
            while len(combined_lines) <= line_index:
                combined_lines.append([])
            combined_lines[line_index].extend(line)
    return [line for line in combined_lines if line]


def nested_header_contains_pruefidentifikatoren(table: Table) -> bool:
    """
    Checks if the header row of a table in the nested layout contains a 'Prüfidentifikator' line with at least one
    Prüfidentifikator (some tables, e.g. in the APERAK AHB, have the line but no Prüfidentifikatoren).
    """
    for line in get_lines_of_outer_row(table, 0):
        if any(cell.text == "Prüfidentifikator" for cell in line):
            return any(_pruefi_pattern.match(cell.text) for cell in line)
    return False


class NestedTableLayout(BaseModel):
    """
    The horizontal layout of an AHB table in the nested layout, derived from its header row.
    """

    pruefi_meta_data: list[PruefiMetaData]
    pruefi_ranges: list[tuple[int, int]]
    beschreibung_x_start: int

    @classmethod
    def from_table(cls, table: Table) -> "NestedTableLayout":
        """
        Reads the header row of the given table.
        The header cell contains an inner table with three rows: 'Beschreibung', 'Kommunikation von' and
        'Prüfidentifikator'. Each Prüfidentifikator defines the horizontal range of its column.
        """
        header_lines = get_lines_of_outer_row(table, 0)
        pruefi_line = next(
            (line for line in header_lines if any(cell.text == "Prüfidentifikator" for cell in line)), None
        )
        if pruefi_line is None:
            raise ValueError("The header of the table contains no line with 'Prüfidentifikator'")
        # might be empty, e.g. for the table in the APERAK AHB which has no Prüfidentifikatoren
        pruefi_cells = [cell for cell in pruefi_line if _pruefi_pattern.match(cell.text)]
        beschreibung_cell = next(
            (cell for line in header_lines for cell in line if cell.text in {"Beschreibung", "Kommunikation von"}),
            None,
        )
        if beschreibung_cell is None:
            raise ValueError("The header of the table contains no 'Beschreibung'")

        def text_above_pruefi(label: str, pruefi_cell: PositionedText) -> str:
            line = next((line for line in header_lines if any(cell.text == label for cell in line)), [])
            best_cell = max(
                (cell for cell in line if cell.text != label),
                key=lambda cell: cell.overlap(pruefi_cell.x_start, pruefi_cell.x_end),
                default=None,
            )
            if best_cell is None or best_cell.overlap(pruefi_cell.x_start, pruefi_cell.x_end) == 0:
                return ""
            return best_cell.text

        pruefi_meta_data = [
            PruefiMetaData(
                pruefidentifikator=pruefi_cell.text,
                name=text_above_pruefi("Beschreibung", pruefi_cell),
                communication_direction=text_above_pruefi("Kommunikation von", pruefi_cell),
            )
            for pruefi_cell in pruefi_cells
        ]
        return cls(
            pruefi_meta_data=pruefi_meta_data,
            pruefi_ranges=[(cell.x_start, cell.x_end) for cell in pruefi_cells],
            beschreibung_x_start=min(
                cell.x_start for line in header_lines for cell in line if cell.text == beschreibung_cell.text
            ),
        )

    @property
    def pruefi_section_end(self) -> int:
        """the right edge of the right-most Prüfidentifikator column; the 'Bedingung' column starts here"""
        return max(x_end for _, x_end in self.pruefi_ranges)

    def get_pruefidentifikatoren(self) -> list[str]:
        """the Prüfidentifikatoren in the order of the table header"""
        return [meta_data.pruefidentifikator for meta_data in self.pruefi_meta_data]

    def _find_pruefi_column(self, cell: PositionedText) -> str | None:
        """
        Returns the Prüfidentifikator whose column overlaps the given cell the most (if any).
        The overlap has to cover at least half of the cell or half of the column, because the expression cells are
        sometimes merged with the empty spacer cell to their left (e.g. in tables with only one Prüfidentifikator).
        """
        best_overlap, best_pruefi = 0, None
        for (x_start, x_end), pruefi in zip(self.pruefi_ranges, self.get_pruefidentifikatoren(), strict=True):
            overlap = cell.overlap(x_start, x_end)
            if overlap > best_overlap and 2 * overlap >= min(cell.x_end - cell.x_start, x_end - x_start):
                best_overlap, best_pruefi = overlap, pruefi
        return best_pruefi

    def _is_at_start_of_middle_section(self, cell: PositionedText) -> bool:
        """
        Checks if the cell starts at the left edge of the middle section, where the codes and qualifiers are.
        The descriptions start further right (roughly at a quarter of the middle section).
        """
        middle_section_width = self.pruefi_ranges[0][0] - self.beschreibung_x_start
        return cell.x_start < self.beschreibung_x_start + 0.12 * middle_section_width

    def _assign_line(self, line: list[PositionedText], row: dict[str, str]) -> None:
        """writes the texts of one line into the columns of the given row"""
        for cell in sorted(line, key=lambda cell: cell.x_start):
            if cell.x_center < self.beschreibung_x_start:
                _assign_edifact_struktur_text(cell.text, row)
            elif (pruefi := self._find_pruefi_column(cell)) is not None:
                row[pruefi] = _join(row[pruefi], cell.text)
            elif cell.x_center > self.pruefi_section_end:
                row["Bedingung"] = _join(row["Bedingung"], cell.text)
            elif self._is_at_start_of_middle_section(cell):
                # free text without code (e.g. 'Nachrichten-Referenznummer') starts at the left edge of the middle
                # section, too. Like the parser for the old layout, we put it into the column for the codes.
                row["Codes und Qualifier"] = _join(row["Codes und Qualifier"], cell.text)
            elif cell.x_center < self.pruefi_ranges[0][0]:
                row["Beschreibung"] = _join(row["Beschreibung"], cell.text)
            else:
                logger.warning("Could not assign text '%s' to any column", cell.text)

    def parse_table(self, table: Table, column_headers: list[str]) -> pd.DataFrame:
        """
        Parses all rows (except for the header) of the given table into a dataframe with the given columns.
        Each line of an outer row results in a row of the dataframe. As in the old layout, the 'Bedingung' text of an
        outer row is attached to its last line.
        """
        rows: list[dict[str, str]] = []
        number_of_rows = len(table._tbl.tr_lst)  # pylint:disable=protected-access
        for row_index in range(1, number_of_rows):
            lines = get_lines_of_outer_row(table, row_index)
            if not lines:
                continue
            bedingung_cells = [cell for line in lines for cell in line if cell.x_center > self.pruefi_section_end]
            new_rows: list[dict[str, str]] = []
            for line in lines:
                row = dict.fromkeys(column_headers, "")
                self._assign_line([cell for cell in line if cell not in bedingung_cells], row)
                if any(value for value in row.values()):
                    new_rows.append(row)
            if not new_rows:
                new_rows.append(dict.fromkeys(column_headers, ""))
            if bedingung_cells:
                new_rows[-1]["Bedingung"] = BedingungCell.beautify_bedingungen(
                    " ".join(cell.text for cell in bedingung_cells)
                )
            rows.extend(new_rows)
        return pd.DataFrame(rows, columns=column_headers, dtype="str")


def _join(existing_text: str, text: str) -> str:
    return f"{existing_text} {text}" if existing_text else text


def _assign_edifact_struktur_text(text: str, row: dict[str, str]) -> None:
    """
    Puts a text from the 'EDIFACT Struktur' column into the appropriate column.
    Texts that are neither segment group, segment, data element nor segment ID are segment names, which the old
    parser puts into the 'Segment Gruppe' column, too.
    """
    if _segment_group_pattern.match(text):
        row["Segment Gruppe"] = text
    elif _segment_pattern.match(text):
        row["Segment"] = text
    elif _data_element_pattern.match(text):
        row["Datenelement"] = text
    elif _segment_id_pattern.match(text):
        row["Segment ID"] = text
    else:
        row["Segment Gruppe"] = _join(row["Segment Gruppe"], text)
