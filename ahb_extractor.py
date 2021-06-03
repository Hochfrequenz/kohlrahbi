from pathlib import Path
from typing import List

import docx
import numpy as np
import pandas as pd

directory_path = Path.cwd() / "documents"
file_name = "UTILMD_AHB_WiM_3_1c_2021_04_01_2021_03_30.docx"

path_to_file = directory_path / file_name

from enum import Enum


class row_type(Enum):
    SEGMENTNAME = 1
    SEGMENTGRUPPE = 2
    SEGMENT = 3
    DATENELEMENT = 4
    HEADER = 5


def create_list_of_column_indices(table):
    """
    The amount of columns of the tables can switch between 3 and 4.
    If the actual table contains the header with "EDIFACT Struktur", then the table has 4 columns.
    The second and the third one have exactly the same content. So we skip the third one to get the same length for the list.
    """
    number_of_columns: int = table._column_count

    if number_of_columns == 3:
        return [0, 1, 2]
    elif number_of_columns == 4:
        return [0, 1, 3]
    else:
        raise NotImplemented(
            f"Only tables with 3 and 4 columns are implemented. Your table has {number_of_columns} columns."
        )


def write_segment_name_to_dataframe(final_dataframe, row_index, dataframe_row, text_in_row_as_list):
    dataframe_row[0] = text_in_row_as_list[0]
    final_dataframe.loc[row_index] = dataframe_row


def write_segmentgruppe_to_dataframe(final_dataframe, row_index, dataframe_row, text_in_row_as_list):
    dataframe_row[0] = text_in_row_as_list[0]

    if text_in_row_as_list[1].count("\t") == 3:
        # example for text_in_row_as_list: ['SG2', '\tMuss\tMuss\tMuss', '']
        splitted_middle_column = text_in_row_as_list[1].split("\t")
        dataframe_row[5] = splitted_middle_column[1]
        dataframe_row[6] = splitted_middle_column[2]
        dataframe_row[7] = splitted_middle_column[3]

    final_dataframe.loc[row_index] = dataframe_row


def write_segment_to_dataframe(final_dataframe, row_index, dataframe_row, text_in_row_as_list):
    splitted_edifact_struktur_cell = text_in_row_as_list[0].split("\t")
    dataframe_row[0] = splitted_edifact_struktur_cell[0]
    dataframe_row[1] = splitted_edifact_struktur_cell[1]

    splitted_middle_cell = text_in_row_as_list[1].split("\t")
    if text_in_row_as_list[1].count("\t") == 3:
        dataframe_row[5] = splitted_middle_cell[0]
        dataframe_row[6] = splitted_middle_cell[1]
        dataframe_row[7] = splitted_middle_cell[2]

    final_dataframe.loc[row_index] = dataframe_row


def write_dataelement_to_dataframe(final_dataframe, row_index, dataframe_row, text_in_row_as_list, middle_cell):

    splitted_edifact_struktur_cell = text_in_row_as_list[0].split("\t")
    if text_in_row_as_list[0].count("\t") == 1:
        dataframe_row[1] = splitted_edifact_struktur_cell[0]
        dataframe_row[2] = splitted_edifact_struktur_cell[1]

    # here we can also distinguish between Freitext (graue Schrift Felder) und nicht Freitext (fette geschriebene Felder)
    if middle_cell.paragraphs[0].runs[0].bold:
        if "\n" in middle_cell.text:

            if middle_cell.text.count("\t") == 5:
                # example: ['UNH\t0065', 'UTILM\tNetzanschluss-\tX\tX\tX\nD\tStammdaten', '']
                splitted_text_at_line_endings: List = middle_cell.text.split("\n")

                splitted_text_at_tabs = [snippet.split("\t") for snippet in splitted_text_at_line_endings]

                fixed_text = [text[0] + text[1] for text in zip(splitted_text_at_tabs[0], splitted_text_at_tabs[1])]

                dataframe_row[3] = fixed_text[0]
                dataframe_row[4] = fixed_text[1]

                dataframe_row[5] = splitted_text_at_tabs[0][2]
                dataframe_row[6] = splitted_text_at_tabs[0][3]
                dataframe_row[7] = splitted_text_at_tabs[0][4]
        else:
            splitted_middle_cell = text_in_row_as_list[1].split("\t")
            if middle_cell.text.count("\t") == 4:
                dataframe_row[3] = splitted_middle_cell[0]
                dataframe_row[4] = splitted_middle_cell[1]
                dataframe_row[5] = splitted_middle_cell[2]
                dataframe_row[6] = splitted_middle_cell[3]
                dataframe_row[7] = splitted_middle_cell[4]

    else:
        splitted_middle_cell = text_in_row_as_list[1].split("\t")
        if text_in_row_as_list[1].count("\t") == 3:
            dataframe_row[3] = splitted_middle_cell[0]
            dataframe_row[5] = splitted_middle_cell[1]
            dataframe_row[6] = splitted_middle_cell[2]
            dataframe_row[7] = splitted_middle_cell[3]

    final_dataframe.loc[row_index] = dataframe_row


def has_cell_in_edifact_struktur_column_a_segmentgruppe(cell):
    # if cell.paragraphs[0].paragraph_format.left_indent == 364490:
    if cell.paragraphs[0].paragraph_format.left_indent == 36830:
        return True
    return False


def is_cell_in_middle_column_a_dataelement(cell):
    # IDEE: ERSTELLE FUNKTION DIE BEREITS DIE GESAMTE ZEILE PRÜFT; WAS SIE IST
    # * segment name: MP-ID Absender
    # * segment gruppe: SG2
    # * segment: SG2\tNAD
    # * datenelement: SG2\tNAD\t3035
    pass


def is_row_header(text_in_row_as_list):
    if text_in_row_as_list[0] == "EDIFACT Struktur":
        return True

    return False


def is_row_segmentname(table, text_in_row_as_list: List) -> bool:
    """
    Checks if the actual row contains just the segment name like "Nachrichten-Kopfsegment"
    """

    # IDEE: ÜBERGEBE DEN FUNKTIONEN NUR NOCH DIE REIHE UND PRÜFE DARAUF DEN ALLES

    # number_of_columns: int = table._column_count

    # if number_of_columns == 4:
    #     if (
    #         text_in_row_as_list[0]
    #         # text_in_row_as_list[1] is skipped cause of redundant structure in 4 column tables
    #         and not text_in_row_as_list[2]
    #         and not text_in_row_as_list[3]
    #     ):
    #         return True

    #     return False

    # elif number_of_columns == 3:
    if text_in_row_as_list[0] and not text_in_row_as_list[1] and not text_in_row_as_list[2]:
        return True

    return False


def is_row_segmentgruppe(edifact_struktur_cell):
    if (
        not edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == 36830
        and not "\t" in edifact_struktur_cell.text
    ):
        return True

    if (
        edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == 36830
        and not "\t" in edifact_struktur_cell.text
    ):
        return True

    return False


def is_row_segment(edifact_struktur_cell):
    # |   UNH    |
    if (
        not edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == 36830
        and not "\t" in edifact_struktur_cell.text
    ):
        return True

    # | SG2\tNAD |
    if (
        edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == 36830
        and edifact_struktur_cell.text.count("\t") == 1
    ):
        return True

    return False


def is_row_datenelement(edifact_struktur_cell):
    # |   UNH\t0062 |
    if (
        not edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == 36830
        and "\t" in edifact_struktur_cell.text
    ):
        return True

    # | SG2\tNAD\t3035 |
    if (
        edifact_struktur_cell.paragraphs[0].paragraph_format.left_indent == 36830
        and edifact_struktur_cell.text.count("\t") == 2
    ):
        return True

    return False

    pass


def define_row_type(table, edifact_struktur_cell, text_in_row_as_list):
    if is_row_header(text_in_row_as_list=text_in_row_as_list):
        return row_type.HEADER

    elif is_row_segmentname(table=table, text_in_row_as_list=text_in_row_as_list):
        return row_type.SEGMENTNAME

    elif is_row_segmentgruppe(edifact_struktur_cell=edifact_struktur_cell):
        return row_type.SEGMENTGRUPPE

    elif is_row_segment(edifact_struktur_cell=edifact_struktur_cell):
        return row_type.SEGMENT

    elif is_row_datenelement(edifact_struktur_cell=edifact_struktur_cell):
        return row_type.DATENELEMENT
    else:
        raise NotImplemented(f"Could not define row type of {text_in_row_as_list}")


# is_row_just_a_segment_name(table=table, text_in_row_as_list=row_cell_texts_as_list)


def main():
    try:
        doc = docx.Document(path_to_file)  # Creating word reader object.

        # TODO for each section get header to get prüfidentifaktoren for dataframe header

        actual_df_row_index: int = 0
        # df = pd.DataFrame(columns=["text", "tab1", "tab2", "tab3", "tab4", "tab5"])
        df = pd.DataFrame(
            columns=[
                "Segment Gruppe",
                "Segment",
                "Datenelement",
                "Codes und Qualifier",
                "Beschreibung",
                "11039",  # should be taken from table header
                "11040",  # should be taken from table header
                "11041",  # should be taken from table header
                "Bedingung",
            ],
            dtype="str",
        )

        # for table in doc.tables[2 : len(doc.tables)]:
        for table in doc.tables[1:20]:

            column_indices = create_list_of_column_indices(table=table)

            for row in range(len(table.rows)):

                # initial empty list for the next row in the dataframe
                actual_dataframe_row = (len(df.columns)) * [""]

                # idea: cause of double information in 4 column tables, remove entry [2] from row_cell_texts_as_list
                row_cell_texts_as_list = [cell.text for cell in table.row_cells(row)]
                if table._column_count == 4:
                    # remove redundant information for tables with 4 columns
                    del row_cell_texts_as_list[2]

                actual_edifact_struktur_cell = table.row_cells(row)[0]

                # check here for row type
                actual_row_type = define_row_type(
                    table=table,
                    edifact_struktur_cell=actual_edifact_struktur_cell,
                    text_in_row_as_list=row_cell_texts_as_list,
                )
                print(actual_row_type.name)

                # skip table header
                # if row_cell_texts_as_list[0] == "EDIFACT Struktur":
                #     continue

                if actual_row_type is row_type.HEADER:
                    continue

                elif actual_row_type is row_type.SEGMENTNAME:
                    write_segment_name_to_dataframe(
                        final_dataframe=df,
                        row_index=actual_df_row_index,
                        dataframe_row=actual_dataframe_row,
                        text_in_row_as_list=row_cell_texts_as_list,
                    )
                    actual_df_row_index = actual_df_row_index + 1
                    continue

                elif actual_row_type is row_type.SEGMENTGRUPPE:
                    write_segmentgruppe_to_dataframe(
                        final_dataframe=df,
                        row_index=actual_df_row_index,
                        dataframe_row=actual_dataframe_row,
                        text_in_row_as_list=row_cell_texts_as_list,
                    )
                    actual_df_row_index = actual_df_row_index + 1
                    continue

                elif actual_row_type is row_type.SEGMENT:
                    write_segment_to_dataframe(
                        final_dataframe=df,
                        row_index=actual_df_row_index,
                        dataframe_row=actual_dataframe_row,
                        text_in_row_as_list=row_cell_texts_as_list,
                    )
                    actual_df_row_index = actual_df_row_index + 1
                    continue

                elif actual_row_type is row_type.DATENELEMENT:
                    write_dataelement_to_dataframe(
                        final_dataframe=df,
                        row_index=actual_df_row_index,
                        dataframe_row=actual_dataframe_row,
                        text_in_row_as_list=row_cell_texts_as_list,
                        middle_cell=table.row_cells(row)[1],
                    )
                    actual_df_row_index = actual_df_row_index + 1
                    continue

                # distinguish between 4 and 3 column tables
                # if len(table.row_cells(row)) == 3:
                #     # if is_row_segmentname(table=table, text_in_row_as_list=row_cell_texts_as_list):
                #     #     write_segment_name_to_dataframe(
                #     #         final_dataframe=df,
                #     #         row_index=actual_df_row_index,
                #     #         dataframe_row=actual_dataframe_row,
                #     #         text_in_row_as_list=row_cell_texts_as_list,
                #     #     )
                #     #     actual_df_row_index = actual_df_row_index + 1
                #     #     continue

                #     for column_number in column_indices:
                #         actual_cell = table.row_cells(row)[column_number]

                #         # LEFT COLUMN -> 0
                #         # at this left_indent, there is no Segment-Gruppe
                #         if column_number == 0 and not has_cell_in_edifact_struktur_column_a_segmentgruppe(
                #             cell=actual_cell
                #         ):
                #             # Segment and Datenelement in cell, example: "UNH\t0062"
                #             if "\t" in actual_cell.text:
                #                 splitted_edifact_struktur_column: List = actual_cell.text.split("\t")
                #                 # print(splitted_edifact_struktur_column)
                #                 # TODO if someone knows a better way, suggestions are very welcome =)
                #                 actual_dataframe_row[1], actual_dataframe_row[2] = (
                #                     splitted_edifact_struktur_column[0],
                #                     splitted_edifact_struktur_column[1],
                #                 )
                #                 continue
                #             # only Segment in cell, example: "UNH"
                #             else:
                #                 actual_dataframe_row[1] = actual_cell.text
                #                 continue

                #         # MIDDLE COLUMN -> 1
                #         if column_number == 1:
                #             # check if cell is in Segment level
                #             if actual_cell.paragraphs[0].paragraph_format.left_indent is None:
                #                 splitted_middle_column = actual_cell.text.split("\t")
                #                 actual_dataframe_row[5], actual_dataframe_row[6], actual_dataframe_row[7] = (
                #                     splitted_middle_column[1],
                #                     splitted_middle_column[2],
                #                     splitted_middle_column[3],
                #                 )

                #             # check if cell is in Datenelement level
                #             if actual_cell.paragraphs[0].paragraph_format.left_indent == 36830:

                #                 tabs = actual_cell.paragraphs[0].paragraph_format.tab_stops._pPr.tabs

                #                 if "\n" in actual_cell.text:

                #                     # if len(tabs) == 4 and "\t" in cell.text.split("\n")[1]:
                #                     if len(tabs) == 4 and actual_cell.text.count("\t") == 5:
                #                         splitted_text_at_line_endings: List = actual_cell.text.split("\n")

                #                         splitted_text_at_tabs = [
                #                             snippet.split("\t") for snippet in splitted_text_at_line_endings
                #                         ]

                #                         fixed_text = [
                #                             text[0] + text[1]
                #                             for text in zip(splitted_text_at_tabs[0], splitted_text_at_tabs[1])
                #                         ]

                #                         actual_dataframe_row[3], actual_dataframe_row[4] = fixed_text[0], fixed_text[1]

                #                 # example: Nachrichten-Referenznummer
                #                 if len(tabs) == 3:
                #                     splitted_middle_column = actual_cell.text.split("\t")
                #                     (
                #                         actual_dataframe_row[3],
                #                         actual_dataframe_row[5],
                #                         actual_dataframe_row[6],
                #                         actual_dataframe_row[7],
                #                     ) = (
                #                         splitted_middle_column[0],
                #                         splitted_middle_column[1],
                #                         splitted_middle_column[2],
                #                         splitted_middle_column[3],
                #                     )

                #                 if (
                #                     len(tabs) == 4
                #                     and actual_cell.text.count("\t") == 4
                #                     and not "\n" in actual_cell.text
                #                 ):
                #                     splitted_middle_column: List = actual_cell.text.split("\t")
                #                     (
                #                         actual_dataframe_row[3],
                #                         actual_dataframe_row[4],
                #                         actual_dataframe_row[5],
                #                         actual_dataframe_row[6],
                #                         actual_dataframe_row[7],
                #                     ) = (
                #                         splitted_middle_column[0],
                #                         splitted_middle_column[1],
                #                         splitted_middle_column[2],
                #                         splitted_middle_column[3],
                #                         splitted_middle_column[4],
                #                     )

                #                 if len(tabs) == 4 and actual_cell.text.count("\t") == 4 and "\n" in actual_cell.text:
                #                     splitted_middle_column = actual_cell.text.split("\t")
                #                     wrapped_lines = splitted_middle_column[-1].split("\n")
                #                     splitted_middle_column[1] = (
                #                         splitted_middle_column[1] + " " + " ".join(wrapped_lines[1:])
                #                     )
                #                     splitted_middle_column[4] = wrapped_lines[0]
                #                     (
                #                         actual_dataframe_row[3],
                #                         actual_dataframe_row[4],
                #                         actual_dataframe_row[5],
                #                         actual_dataframe_row[6],
                #                         actual_dataframe_row[7],
                #                     ) = (
                #                         splitted_middle_column[0],
                #                         splitted_middle_column[1],
                #                         splitted_middle_column[2],
                #                         splitted_middle_column[3],
                #                         splitted_middle_column[4],
                #                     )

                # # distinguish between 4 and 3 column tables
                # if len(table.row_cells(row)) == 4:

                #     # for cell in table.row_cells(row):

                #     # breakpoint
                #     # row_cell_texts_as_list = [cell.text for cell in table.row_cells(row)]

                #     # Write segment name like "Nachrichten-Kopfsegment"
                #     if is_row_segmentname(table=table, text_in_row_as_list=row_cell_texts_as_list):
                #         actual_dataframe_row[0] = row_cell_texts_as_list[0]
                #         df.loc[actual_df_row_index] = actual_dataframe_row
                #         actual_df_row_index = actual_df_row_index + 1
                #         continue

                #     # for cell in table.row_cells(row):

                #     # ----------------
                #     # middle column is double in four column tables -> skip one column
                #     for column_number in column_indices:
                #         actual_cell = table.row_cells(row)[column_number]

                #         # LEFT COLUMN -> 0
                #         # at this left_indent, there is now Segment-Gruppe
                #         # if column_number == 0 and actual_cell.paragraphs[0].paragraph_format.left_indent == 364490:
                #         if column_number == 0 and not has_cell_in_edifact_struktur_column_a_segmentgruppe(
                #             cell=actual_cell
                #         ):
                #             # Segement and Datenelement in cell, example: "UNH\t0062"
                #             if "\t" in actual_cell.text:
                #                 splitted_edifact_struktur_column: List = actual_cell.text.split("\t")
                #                 # print(splitted_edifact_struktur_column)
                #                 # TODO if someone knows a better way, suggestions are very welcome =)
                #                 actual_dataframe_row[1], actual_dataframe_row[2] = (
                #                     splitted_edifact_struktur_column[0],
                #                     splitted_edifact_struktur_column[1],
                #                 )
                #                 continue
                #             # only Segment in cell, example: "UNH"
                #             else:
                #                 actual_dataframe_row[1] = actual_cell.text
                #                 continue

                #         # MIDDLE COLUMN -> 1
                #         if column_number == 1:
                #             # check if cell is in Segment level
                #             if actual_cell.paragraphs[0].paragraph_format.left_indent is None:
                #                 splitted_middle_column = actual_cell.text.split("\t")
                #                 actual_dataframe_row[5], actual_dataframe_row[6], actual_dataframe_row[7] = (
                #                     splitted_middle_column[1],
                #                     splitted_middle_column[2],
                #                     splitted_middle_column[3],
                #                 )

                #             # check if cell is in Datenelement level
                #             if actual_cell.paragraphs[0].paragraph_format.left_indent == 36830:

                #                 tabs = actual_cell.paragraphs[0].paragraph_format.tab_stops._pPr.tabs

                #                 if "\n" in actual_cell.text:

                #                     # if len(tabs) == 4 and "\t" in cell.text.split("\n")[1]:
                #                     if len(tabs) == 4 and actual_cell.text.count("\t") == 5:
                #                         splitted_text_at_line_endings: List = actual_cell.text.split("\n")

                #                         splitted_text_at_tabs = [
                #                             snippet.split("\t") for snippet in splitted_text_at_line_endings
                #                         ]

                #                         fixed_text = [
                #                             text[0] + text[1]
                #                             for text in zip(splitted_text_at_tabs[0], splitted_text_at_tabs[1])
                #                         ]

                #                         actual_dataframe_row[3], actual_dataframe_row[4] = fixed_text[0], fixed_text[1]

                #                 # example: Nachrichten-Referenznummer
                #                 if len(tabs) == 3:
                #                     splitted_middle_column = actual_cell.text.split("\t")
                #                     (
                #                         actual_dataframe_row[3],
                #                         actual_dataframe_row[5],
                #                         actual_dataframe_row[6],
                #                         actual_dataframe_row[7],
                #                     ) = (
                #                         splitted_middle_column[0],
                #                         splitted_middle_column[1],
                #                         splitted_middle_column[2],
                #                         splitted_middle_column[3],
                #                     )

                #                 if (
                #                     len(tabs) == 4
                #                     and actual_cell.text.count("\t") == 4
                #                     and not "\n" in actual_cell.text
                #                 ):
                #                     splitted_middle_column: List = actual_cell.text.split("\t")
                #                     (
                #                         actual_dataframe_row[3],
                #                         actual_dataframe_row[4],
                #                         actual_dataframe_row[5],
                #                         actual_dataframe_row[6],
                #                         actual_dataframe_row[7],
                #                     ) = (
                #                         splitted_middle_column[0],
                #                         splitted_middle_column[1],
                #                         splitted_middle_column[2],
                #                         splitted_middle_column[3],
                #                         splitted_middle_column[4],
                #                     )

                #                 if len(tabs) == 4 and actual_cell.text.count("\t") == 4 and "\n" in actual_cell.text:
                #                     splitted_middle_column = actual_cell.text.split("\t")
                #                     wrapped_lines = splitted_middle_column[-1].split("\n")
                #                     splitted_middle_column[1] = (
                #                         splitted_middle_column[1] + " " + " ".join(wrapped_lines[1:])
                #                     )
                #                     splitted_middle_column[4] = wrapped_lines[0]
                #                     (
                #                         actual_dataframe_row[3],
                #                         actual_dataframe_row[4],
                #                         actual_dataframe_row[5],
                #                         actual_dataframe_row[6],
                #                         actual_dataframe_row[7],
                #                     ) = (
                #                         splitted_middle_column[0],
                #                         splitted_middle_column[1],
                #                         splitted_middle_column[2],
                #                         splitted_middle_column[3],
                #                         splitted_middle_column[4],
                #                     )

                #                 # Beschreibung -> 4 -> 436245
                #                 # 11039 -> 5 -> 1962785
                #                 # 11040 -> 6 -> 2578735
                #                 # 11041 -> 7 -> 3192780
                #                 # 'UTILM\tNetzanschluss-\tX\tX\tX\nD\tStammdaten'
                #                 # split \n check if \t is in second entry

                #                 # print(actual_cell.text)
                #                 # print(actual_cell.paragraphs[0].paragraph_format.left_indent)

                # df.loc[actual_df_row_index] = actual_dataframe_row

                # actual_df_row_index = actual_df_row_index + 1

                # if cell.paragraphs[0].paragraph_format.left_indent == 364490:

                # Write in column: Segement-Gruppe
                # 'SG2'
                # cell.paragraphs[0].paragraph_format.left_indent -> 36830
                # 'SG2\tNAD'
                # 36830
                # '\tMuss\tMuss\tMuss'
                # None
                # ''
                # None
                # ↩
                # 'SG2\tNAD\t3035'
                # 36830

                # Write in column: Segment
                # 'UNH'
                # cell.paragraphs[0].paragraph_format.left_indent -> 364490

                # print(repr(actual_cell.text))
                # print(actual_cell.paragraphs[0].paragraph_format.left_indent)
                # dataframe_row[0] = repr(cell.text)

                # print(cell.paragraphs[0].paragraph_format.tab_stops)
                # print(cell.paragraphs[0].paragraph_format.tab_stops._pPr)
                # print(cell.paragraphs[0].paragraph_format.tab_stops._pPr.tabs)

                # tabs = cell.paragraphs[0].paragraph_format.tab_stops._pPr.tabs
                # if tabs is not None:

                #     # tab_position_list = (len(df.columns) - 1) * [np.nan]
                #     i = 1
                #     for tab in tabs:
                #         # print(tab.pos)

                #         dataframe_row[i] = tab.pos
                #         i = i + 1
                #         # dataframe_row.append(tab_position_list)

                # df.loc[df_row_index] = dataframe_row

                # df_row_index = df_row_index + 1

                # print(tabs.tag)
                # print(tabs.attrib)
                # print(cell.paragraphs[0].paragraph_format.tab_stops._pPr.tab)
                print("↩")

        df.to_csv("export.csv")
        # df.to_excel("export.xlsx")
        print(len(doc.tables[1].columns))

    except IOError:
        print("There was an error opening the file!")
        return


if __name__ == "__main__":
    main()
