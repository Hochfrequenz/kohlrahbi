"""
A collection of functions to get information from AHB tables.
"""
import re
from pathlib import Path
from typing import List, Tuple

import pandas as pd  # type:ignore[import]
from docx.document import Document  # type:ignore[import]
from docx.oxml.table import CT_Tbl  # type:ignore[import]
from docx.oxml.text.paragraph import CT_P  # type:ignore[import]
from docx.table import Table, _Cell  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]

from ahbextractor.helper.check_row_type import RowType, define_row_type
from ahbextractor.helper.elixir import Elixir
from ahbextractor.helper.export_functions import (
    export_all_pruefidentifikatoren_in_one_file,
    export_single_pruefidentifikator,
)
from ahbextractor.helper.write_functions import write_new_row_in_dataframe

_pruefi_pattern = re.compile(r"^\d{5}$")


def get_all_paragraphs_and_tables(parent):
    """
    Yield each paragraph and table child within *parent*, in document order.
    Each returned value is an instance of either Table or Paragraph.
    *parent* would most commonly be a reference to a main Document object, but
    also works for a _Cell object, which itself can contain paragraphs and tables.
    """
    # pylint: disable=protected-access
    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Passed parent argument must be of type Document or _Cell")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


# pylint: disable=too-many-arguments
def read_table(
    elixir: Elixir,
    table: Table,
) -> Tuple[List[RowType], int]:
    """
    Iterates through all rows in a given table and writes all extracted infos in a DataFrame.

    Args:
        table (Table): Current table in the docx
        dataframe (pd.DataFrame): Contains all infos of the Prüfidentifikators
        current_df_row_index (int): Current row of the dataframe
        last_two_row_types (List[RowType]): Contains the two last RowType. Is needed for the case of empty rows.
        edifact_struktur_cell_left_indent_position (int): Position of the left indent in the
            indicator edifact struktur cell
        middle_cell_left_indent_position (int): Position of the left indent in the indicator middle cell
        tabstop_positions (List[int]): All tabstop positions of the indicator middle cell

    Returns:
        Tuple[List[RowType], int]: Last two RowTypes and the new row index for the DataFrame
    """
    # pylint: disable=protected-access
    if table._column_count == 4:
        index_for_middle_column = 2
    else:
        index_for_middle_column = 1

    for row in range(len(table.rows)):

        # initial empty list for the next row in the dataframe
        elixir.soul.loc[elixir.current_df_row_index] = (len(elixir.soul.columns)) * [""]

        row_cell_texts_as_list = [cell.text for cell in table.row_cells(row)]

        # pylint: disable=protected-access
        if table._column_count == 4:
            # remove redundant information for tables with 4 columns
            if (
                row_cell_texts_as_list[0] == row_cell_texts_as_list[1]
                and row_cell_texts_as_list[2] == row_cell_texts_as_list[3]
            ):
                # pylint: disable=line-too-long
                # HEADER looks like
                # 0:'EDIFACT Struktur'
                # 1:'EDIFACT Struktur'
                # 2:'Beschreibung\tKündigung\tBestätigung\tAblehnung\tBedingung\n\tMSB \tKündigung\tKündigung\n\tMSB \tMSB \nKommunikation von\tMSBN an\tMSBA an\tMSBA an\n\tMSBA\tMSBN\tMSBN\nPrüfidentifikator\t11039\t11040\t11041'
                # 3:'Beschreibung\tKündigung\tBestätigung\tAblehnung\tBedingung\n\tMSB \tKündigung\tKündigung\n\tMSB \tMSB \nKommunikation von\tMSBN an\tMSBA an\tMSBA an\n\tMSBA\tMSBN\tMSBN\nPrüfidentifikator\t11039\t11040\t11041'
                # len():4
                del row_cell_texts_as_list[1]
                row_cell_texts_as_list[2] = ""
            elif row_cell_texts_as_list[1] == row_cell_texts_as_list[2]:
                # Dataelement row with header in the table
                # 0:'SG2\tNAD\t3035'
                # 1:'SG2\tNAD\t3035'
                # 2:'MR\tNachrichtenempfänger\tX\tX\tX'
                # 3:''
                # len():4
                del row_cell_texts_as_list[1]
            elif row_cell_texts_as_list[0] == row_cell_texts_as_list[1]:
                del row_cell_texts_as_list[1]

        current_edifact_struktur_cell = table.row_cells(row)[0]

        # check for row type
        current_row_type = define_row_type(
            edifact_struktur_cell=current_edifact_struktur_cell,
            left_indent_position=elixir.edifact_struktur_left_indent_position,
        )

        # write actual row into dataframe
        if not (current_row_type is RowType.EMPTY and elixir.last_two_row_types[0] is RowType.HEADER):
            write_new_row_in_dataframe(
                row_type=current_row_type,
                table=table,
                row=row,
                index_for_middle_column=index_for_middle_column,
                elixir=elixir,
            )

        else:
            write_new_row_in_dataframe(
                row_type=elixir.last_two_row_types[1],
                table=table,
                row=row,
                index_for_middle_column=index_for_middle_column,
                elixir=elixir,
            )

        # remember last row type for empty cells
        elixir.last_two_row_types[1] = elixir.last_two_row_types[0]
        elixir.last_two_row_types[0] = current_row_type

    return elixir.last_two_row_types, elixir.current_df_row_index


# pylint: disable=inconsistent-return-statements
def get_ahb_extract(document: Document, output_directory_path: Path, ahb_file_name: Path) -> int:
    """Reads a docx file and extracts all information for each Prüfidentifikator.

    Args:
        document (Document): AHB which is read by python-docx package
        output_directory_path (Path): Location of the output files
        ahb_file_name (str): Name of the AHB document

    Returns:
        int: Error code, 0 means success
    """

    pruefidentifikatoren: List = []

    # Iterate through the whole word document
    for item in get_all_paragraphs_and_tables(parent=document):

        # Check if there is just a text paragraph,
        if isinstance(item, Paragraph) and not "Heading" in item.style.name:
            continue

        # Check if the paragraph is a chapter or section title
        if isinstance(item, Paragraph) and "Heading" in item.style.name:
            current_chapter_title = item.text

            # Stop iterating at the section "Änderungshistorie"
            if current_chapter_title == "Änderungshistorie":
                # export last pruefidentifikatoren in AHB
                for pruefi in pruefidentifikatoren:

                    export_single_pruefidentifikator(
                        pruefi=pruefi,
                        df=df,
                        output_directory_path=output_directory_path,
                    )

                    export_all_pruefidentifikatoren_in_one_file(
                        pruefi=pruefi,
                        df=df,
                        output_directory_path=output_directory_path,
                        file_name=ahb_file_name,
                    )

                # I don't know how to exit the program without a return
                return 0

        # Check if a table comes with new Prüfidentifikatoren
        elif isinstance(item, Table) and item.cell(row_idx=0, col_idx=0).text == "EDIFACT Struktur":
            # before we go to the next pruefidentifikatoren we save the current ones
            # but at the first loop we check if list of pruefidentifikatoren is empty
            if pruefidentifikatoren:
                for pruefi in pruefidentifikatoren:

                    export_single_pruefidentifikator(
                        pruefi=pruefi,
                        df=df,
                        output_directory_path=output_directory_path,
                    )

                    export_all_pruefidentifikatoren_in_one_file(
                        pruefi=pruefi,
                        df=df,
                        output_directory_path=output_directory_path,
                        file_name=ahb_file_name,
                    )

            elixir = Elixir.from_table(docx_table=item)

            print("\n🔍 Extracting Pruefidentifikatoren:", ", ".join(elixir.pruefidentifikatoren))

            read_table(
                elixir=elixir,
                table=item,
            )

            is_initial_run = False

        elif isinstance(item, Table) and "elixir" in locals():
            read_table(
                elixir=elixir,
                table=item,
            )
    return 0  # you need to return something when the type hint states that you return something
