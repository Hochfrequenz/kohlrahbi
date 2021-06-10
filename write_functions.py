from typing import List

import pandas as pd
from docx.text.paragraph import Paragraph

from check_row_type import RowType


def parse_paragraph_in_middle_column_to_dataframe(
    paragraph: Paragraph,
    dataframe: pd.DataFrame,
    row_index: int,
    dataframe_row: List,
    left_indent_position: int,
    tabstop_positions: List,
):

    # Codenummer, e.g. 332 or
    # Freitext, e.g. Vorgangsnummer

    splitted_text_at_tabs = paragraph.text.split("\t")

    # Qualifier / Code
    # left_indent_position is characteristic for Datenelemente
    if paragraph.paragraph_format.left_indent == left_indent_position:
        dataframe.at[row_index, "Codes und Qualifier"] += splitted_text_at_tabs.pop(0)
        column_indezes = list(range(4, 4 + len(tabstop_positions)))

    elif splitted_text_at_tabs[0] == "":
        tabstop_positions = tabstop_positions[1:]
        del splitted_text_at_tabs[0]

        column_indezes = list(range(5, 5 + len(tabstop_positions)))

    for tabstop in paragraph.paragraph_format.tab_stops._pPr.tabs:
        for tabstop_position, column_index in zip(tabstop_positions, column_indezes):
            if tabstop.pos == tabstop_position:
                dataframe.iat[row_index, column_index] += splitted_text_at_tabs.pop(0)

    return dataframe_row


def write_segment_name_to_dataframe(dataframe, row_index, text_in_row_as_list):
    dataframe.at[row_index, "Segment Gruppe"] = text_in_row_as_list[0]


def write_segmentgruppe_to_dataframe(
    dataframe,
    row_index,
    dataframe_row,
    text_in_row_as_list,
    middle_cell,
    left_indent_position: int,
    tabstop_positions: List,
):
    dataframe.at[row_index, "Segment Gruppe"] = text_in_row_as_list[0]

    # Write Bedingung
    dataframe.at[row_index, "Bedingung"] += text_in_row_as_list[2]

    # Check if there are any tabstops in the middle cell
    if middle_cell.paragraphs[0].paragraph_format.tab_stops._pPr.tabs is None:
        pass
    else:
        for paragraph in middle_cell.paragraphs:
            dataframe_row = parse_paragraph_in_middle_column_to_dataframe(
                paragraph=paragraph,
                dataframe=dataframe,
                row_index=row_index,
                dataframe_row=dataframe_row,
                left_indent_position=left_indent_position,
                tabstop_positions=tabstop_positions,
            )

    # check if there is some text in EDIFACT Struktur cell
    if dataframe_row[0]:
        dataframe.loc[row_index] = dataframe_row
        pass
    else:
        dataframe_row = [a + " " + b for a, b in zip(list(dataframe.loc[row_index]), dataframe_row)]
        dataframe.loc[row_index] = dataframe_row


def write_segment_to_dataframe(
    dataframe,
    row_index,
    dataframe_row,
    text_in_row_as_list,
    middle_cell,
    left_indent_position: int,
    tabstop_positions: List,
):
    splitted_edifact_struktur_cell = text_in_row_as_list[0].split("\t")

    if len(splitted_edifact_struktur_cell) == 1:
        # Example: "UNH"
        dataframe.at[row_index, "Segment"] = splitted_edifact_struktur_cell[0]
    else:
        dataframe.at[row_index, "Segment Gruppe"] = splitted_edifact_struktur_cell[0]
        dataframe.at[row_index, "Segment"] = splitted_edifact_struktur_cell[1]

    # Write Bedingung
    if middle_cell.text == "":
        dataframe.at[row_index, "Bedingung"] += text_in_row_as_list[2]
    else:
        dataframe.at[row_index, "Bedingung"] += text_in_row_as_list[2]
        for paragraph in middle_cell.paragraphs:
            dataframe_row = parse_paragraph_in_middle_column_to_dataframe(
                paragraph=paragraph,
                dataframe=dataframe,
                row_index=row_index,
                dataframe_row=dataframe_row,
                left_indent_position=left_indent_position,
                tabstop_positions=tabstop_positions,
            )


def count_matching(condition, seq):
    """Returns the amount of items in seq that return true from condition"""
    return sum(condition(item) for item in seq)


def code_condition(paragraph):
    try:
        tabstop_positions = [tab_position.pos for tab_position in paragraph.paragraph_format.tab_stops._pPr.tabs]
    except TypeError:
        return False

    if paragraph.runs[0].bold == True and any(x in tabstop_positions for x in [1962785, 2578735, 3192780]):
        return True
    return False


def has_middle_cell_multiple_codes(paragraphs) -> bool:

    if count_matching(code_condition, paragraphs) > 1:
        return True
    return False


def write_dataelement_to_dataframe(
    dataframe,
    row_index,
    dataframe_row,
    text_in_row_as_list,
    middle_cell,
    left_indent_position: int,
    tabstop_positions: List,
):

    # EDIFACT STRUKTUR COLUMN
    splitted_edifact_struktur_cell = text_in_row_as_list[0].split("\t")
    if text_in_row_as_list[0].count("\t") == 1:
        # Example: "UNH\t0062"
        dataframe.at[row_index, "Segment"] = splitted_edifact_struktur_cell[0]
        dataframe.at[row_index, "Datenelement"] = splitted_edifact_struktur_cell[1]

    elif text_in_row_as_list[0].count("\t") == 2:
        dataframe.at[row_index, "Segment Gruppe"] = splitted_edifact_struktur_cell[0]
        dataframe.at[row_index, "Segment"] = splitted_edifact_struktur_cell[1]
        dataframe.at[row_index, "Datenelement"] = splitted_edifact_struktur_cell[2]
    # here we can also distinguish between Freitext (graue Schrift Felder) und nicht Freitext (fette geschriebene Felder)
    # if middle_cell.paragraphs[0].runs[0].bold:

    # MIDDLE COLUMN
    if "\t" in middle_cell.text:
        # Write Bedingung
        dataframe.at[row_index, "Bedingung"] = text_in_row_as_list[2]

        if len(middle_cell.paragraphs) == 1:
            # -> single line row
            dataframe_row = parse_paragraph_in_middle_column_to_dataframe(
                paragraph=middle_cell.paragraphs[0],
                dataframe=dataframe,
                row_index=row_index,
                dataframe_row=dataframe_row,
                left_indent_position=left_indent_position,
                tabstop_positions=tabstop_positions,
            )
            row_index = row_index + 1
        elif has_middle_cell_multiple_codes(paragraphs=middle_cell.paragraphs):
            # here we have to look into the next row to see, if we can add a new datarow or
            # if we have to collect more information in the next row and then add a new datarow
            create_new_dataframe_row_indicator_list: List = [
                paragraph.runs[0].bold == True for paragraph in middle_cell.paragraphs
            ]

            for paragraph, i in zip(middle_cell.paragraphs, range(len(create_new_dataframe_row_indicator_list))):

                if paragraph.runs[0].bold:
                    dataframe_row = parse_paragraph_in_middle_column_to_dataframe(
                        paragraph=paragraph,
                        dataframe=dataframe,
                        row_index=row_index,
                        dataframe_row=dataframe_row,
                        left_indent_position=left_indent_position,
                        tabstop_positions=tabstop_positions,
                    )

                elif paragraph.paragraph_format.left_indent == tabstop_positions[0]:
                    # multi line Beschreibung
                    dataframe.at[row_index, "Beschreibung"] += " " + paragraph.text

                if len(create_new_dataframe_row_indicator_list) > i + 1:
                    if create_new_dataframe_row_indicator_list[i + 1]:
                        dataframe.loc[row_index] = dataframe_row
                        row_index = row_index + 1
                        dataframe.loc[row_index] = (len(dataframe.columns)) * [""]
                else:
                    row_index = row_index + 1

        else:
            # multiline dataelements which are multiline caused by too long text
            for paragraph in middle_cell.paragraphs:

                if paragraph.paragraph_format.left_indent == left_indent_position and "\t" in paragraph.text:

                    dataframe_row = parse_paragraph_in_middle_column_to_dataframe(
                        paragraph=paragraph,
                        dataframe=dataframe,
                        row_index=row_index,
                        dataframe_row=dataframe_row,
                        left_indent_position=left_indent_position,
                        tabstop_positions=tabstop_positions,
                    )

                elif paragraph.paragraph_format.left_indent == left_indent_position and not "\t" in paragraph.text:
                    # multi line Freitext
                    dataframe.at[row_index, "Codes und Qualifier"] += " " + paragraph.text
                elif paragraph.paragraph_format.left_indent == tabstop_positions[0]:
                    # multi line Beschreibung
                    dataframe.at[row_index, "Beschreibung"] += " " + paragraph.text
                elif paragraph.paragraph_format.left_indent is None:
                    parse_paragraph_in_middle_column_to_dataframe(
                        paragraph=paragraph,
                        dataframe=dataframe,
                        row_index=row_index,
                        dataframe_row=dataframe_row,
                        left_indent_position=left_indent_position,
                        tabstop_positions=tabstop_positions,
                    )
                else:
                    raise NotImplementedError(f"The row with {repr(paragraph.text)} can not be read.")

            row_index = row_index + 1

    else:
        # we come to this case if the EDIFACT Struktur cell is empty
        for paragraph in middle_cell.paragraphs:
            if paragraph.paragraph_format.left_indent == 36830 and not "\t" in paragraph.text:
                # multi line Freitext
                dataframe.at[row_index, "Codes und Qualifier"] += text_in_row_as_list[2]

        # Write Bedingung
        dataframe.at[row_index, "Bedingung"] += text_in_row_as_list[2]
    return row_index


def write_new_row_in_dataframe(
    row_type,
    table,
    row,
    index_for_middle_column,
    dataframe,
    dataframe_row_index,
    dataframe_row,
    row_cell_texts_as_list,
    left_indent_position,
    tabstop_positions,
):
    if row_type is RowType.HEADER:
        pass

    elif row_type is RowType.SEGMENTNAME:
        write_segment_name_to_dataframe(
            dataframe=dataframe,
            row_index=dataframe_row_index,
            text_in_row_as_list=row_cell_texts_as_list,
        )
        dataframe_row_index = dataframe_row_index + 1

    elif row_type is RowType.SEGMENTGRUPPE:
        write_segmentgruppe_to_dataframe(
            dataframe=dataframe,
            row_index=dataframe_row_index,
            dataframe_row=dataframe_row,
            text_in_row_as_list=row_cell_texts_as_list,
            middle_cell=table.row_cells(row)[index_for_middle_column],
            left_indent_position=left_indent_position,
            tabstop_positions=tabstop_positions,
        )
        dataframe_row_index = dataframe_row_index + 1

    elif row_type is RowType.SEGMENT:
        write_segment_to_dataframe(
            dataframe=dataframe,
            row_index=dataframe_row_index,
            dataframe_row=dataframe_row,
            text_in_row_as_list=row_cell_texts_as_list,
            middle_cell=table.row_cells(row)[index_for_middle_column],
            left_indent_position=left_indent_position,
            tabstop_positions=tabstop_positions,
        )
        dataframe_row_index = dataframe_row_index + 1

    elif row_type is RowType.DATENELEMENT:
        dataframe_row_index = write_dataelement_to_dataframe(
            dataframe=dataframe,
            row_index=dataframe_row_index,
            dataframe_row=dataframe_row,
            text_in_row_as_list=row_cell_texts_as_list,
            middle_cell=table.row_cells(row)[index_for_middle_column],
            left_indent_position=left_indent_position,
            tabstop_positions=tabstop_positions,
        )

    elif row_type is RowType.EMPTY:
        pass

    return dataframe_row_index
