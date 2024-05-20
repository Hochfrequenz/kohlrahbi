"""
This module provides a class to collect information which of need for all parsing functions
"""

from docx.table import Table
from pydantic import BaseModel, Field

from kohlrahbi.enums import RowType
from kohlrahbi.table_header import PruefiMetaData, TableHeader, get_tabstop_positions


# pylint: disable=too-few-public-methods
class Seed(BaseModel):
    """
    helper class to store all values to extract the AHB and the final AHB as dataframe
    """

    pruefidentifikatoren: list[str] = Field(default_factory=list)
    column_headers: list[str] = Field(default_factory=list)
    edifact_struktur_left_indent_position: int = 0
    middle_cell_left_indent_position: int = 0
    tabstop_positions: list[int] = Field(default_factory=list)
    last_two_row_types: list[RowType] = Field(default_factory=list)
    metadata: list[PruefiMetaData] = Field(default_factory=list)

    # why this classmethod?
    # to decouple the data structure of Elixir from the input data
    # more information can be found on https://www.attrs.org/en/stable/init.html#initialization
    @classmethod
    def from_table(cls, docx_table: Table) -> "Seed":
        """Prepare DataFrame for a new table with new Prüfidentifikatoren

        Args:
            item (Union[Paragraph, Table]): A paragraph or table from the docx
        """

        # the header cell with all pruefi information is the last cell in the first row
        # the first row contains the 'EDIFACT Struktur' column, which is not needed
        # often there is a second row with the pruefidentifikatoren information but it is not reliable for all tables
        # therefore we use the last cell in the first row which seems to be the most reliable
        header_cell_with_all_pruefi_information = docx_table.row_cells(0)[-1]

        table_header = TableHeader.from_header_cell(row_cell=header_cell_with_all_pruefi_information)

        pruefidentifikatoren = table_header.get_pruefidentifikatoren()

        # edifact struktur cell
        edifact_struktur_indicator_paragraph = docx_table.cell(row_idx=4, col_idx=0).paragraphs[0]
        edifact_struktur_left_indent_position = edifact_struktur_indicator_paragraph.paragraph_format.left_indent

        # middle cell
        middle_cell_indicator_paragraph = docx_table.cell(row_idx=4, col_idx=1).paragraphs[0]
        middle_cell_left_indent_position = middle_cell_indicator_paragraph.paragraph_format.left_indent
        tabstop_positions = get_tabstop_positions(middle_cell_indicator_paragraph)

        # metadata
        metadata = table_header.pruefi_meta_data

        base_column_names: list[str] = [
            "Segment Gruppe",
            "Segment",
            "Datenelement",
            "Codes und Qualifier",
            "Beschreibung",
        ]
        columns = base_column_names + pruefidentifikatoren + ["Bedingung"]

        # Initialize help variables
        last_two_row_types: list[RowType] = [RowType.EMPTY, RowType.EMPTY]

        return cls(
            pruefidentifikatoren=pruefidentifikatoren,
            column_headers=columns,
            edifact_struktur_left_indent_position=edifact_struktur_left_indent_position,
            middle_cell_left_indent_position=middle_cell_left_indent_position,
            tabstop_positions=tabstop_positions,
            last_two_row_types=last_two_row_types,
            metadata=metadata,
        )
