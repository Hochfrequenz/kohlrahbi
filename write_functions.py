from typing import List

from check_row_type import RowType


def parse_paragraph_in_middle_column_to_dataframe(paragraph, dataframe_row):

    # Codenummer, e.g. 332 or
    # Freitext, e.g. Vorgangsnummer

    splitted_text_at_tabs = paragraph.text.split("\t")

    # Qualifier / Code
    dataframe_row[3] += splitted_text_at_tabs.pop(0)

    for tabstop in paragraph.paragraph_format.tab_stops._pPr.tabs:
        if tabstop.pos == 436245:
            # Beschreibung
            dataframe_row[4] += splitted_text_at_tabs.pop(0)
        elif tabstop.pos == 1962785:
            # first Prüfidentifikator
            dataframe_row[5] += splitted_text_at_tabs.pop(0)
        elif tabstop.pos == 2578735:
            # second Prüfidentifikator
            dataframe_row[6] += splitted_text_at_tabs.pop(0)
        elif tabstop.pos == 3192780:
            # third Prüfidentifikator
            dataframe_row[7] += splitted_text_at_tabs.pop(0)
        else:
            raise NotImplementedError(
                f"Found an undefined tabstop position: {tabstop.pos}. Text: {splitted_text_at_tabs}"
            )
    return dataframe_row


def write_segment_name_to_dataframe(dataframe, row_index, dataframe_row, text_in_row_as_list):
    dataframe_row[0] = text_in_row_as_list[0]
    dataframe.loc[row_index] = dataframe_row


def write_segmentgruppe_to_dataframe(dataframe, row_index, dataframe_row, text_in_row_as_list, middle_cell):
    dataframe_row[0] = text_in_row_as_list[0]
    # Write Bedingung
    dataframe_row[8] += text_in_row_as_list[2]

    # Check if there are any tabstops in the middle cell
    if middle_cell.paragraphs[0].paragraph_format.tab_stops._pPr.tabs is None:
        pass
    else:
        for paragraph in middle_cell.paragraphs:
            dataframe_row = parse_paragraph_in_middle_column_to_dataframe(
                paragraph=paragraph, dataframe_row=dataframe_row
            )

    # check if there is some text in EDIFACT Struktur cell
    if dataframe_row[0]:
        dataframe.loc[row_index] = dataframe_row
        pass
    else:
        dataframe_row = [a + " " + b for a, b in zip(list(dataframe.loc[row_index]), dataframe_row)]
        dataframe.loc[row_index] = dataframe_row


def write_segment_to_dataframe(dataframe, row_index, dataframe_row, text_in_row_as_list, middle_cell):
    splitted_edifact_struktur_cell = text_in_row_as_list[0].split("\t")

    # Write Bedingung
    dataframe_row[8] = text_in_row_as_list[2]

    if len(splitted_edifact_struktur_cell) == 1:
        dataframe_row[1] = splitted_edifact_struktur_cell[0]
    else:
        dataframe_row[0] = splitted_edifact_struktur_cell[0]
        dataframe_row[1] = splitted_edifact_struktur_cell[1]

    for paragraph in middle_cell.paragraphs:
        dataframe_row = parse_paragraph_in_middle_column_to_dataframe(paragraph=paragraph, dataframe_row=dataframe_row)

    dataframe.loc[row_index] = dataframe_row


def count_matching(condition, seq):
    """Returns the amount of items in seq that return true from condition"""
    # return sum(1 for item in seq if condition(item))

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


def write_dataelement_to_dataframe(dataframe, row_index, dataframe_row, text_in_row_as_list, middle_cell):

    # Write Bedingung
    dataframe_row[8] = text_in_row_as_list[2]

    splitted_edifact_struktur_cell = text_in_row_as_list[0].split("\t")
    if text_in_row_as_list[0].count("\t") == 1:
        # EDIFACT Struktur column: UNH\t0062
        dataframe_row[1] = splitted_edifact_struktur_cell[0]
        dataframe_row[2] = splitted_edifact_struktur_cell[1]
    elif text_in_row_as_list[0].count("\t") == 2:
        dataframe_row[0] = splitted_edifact_struktur_cell[0]
        dataframe_row[1] = splitted_edifact_struktur_cell[1]
        dataframe_row[2] = splitted_edifact_struktur_cell[2]

    # here we can also distinguish between Freitext (graue Schrift Felder) und nicht Freitext (fette geschriebene Felder)
    # if middle_cell.paragraphs[0].runs[0].bold:

    if len(middle_cell.paragraphs) == 1:
        # -> single line row
        dataframe_row = parse_paragraph_in_middle_column_to_dataframe(
            paragraph=middle_cell.paragraphs[0], dataframe_row=dataframe_row
        )
        dataframe.loc[row_index] = dataframe_row
        row_index = row_index + 1
    elif has_middle_cell_multiple_codes(paragraphs=middle_cell.paragraphs):
        # here we have to look into the next row to see, if we can add a new datarow or
        # if we have to collect more information in the next row and then add a new datarow
        create_new_dataframe_row_indicator_list: List = [
            paragraph.runs[0].bold == True for paragraph in middle_cell.paragraphs
        ]

        for paragraph, i in zip(middle_cell.paragraphs, range(len(create_new_dataframe_row_indicator_list))):
            # for paragraph in middle_cell.paragraphs:

            if paragraph.runs[0].bold:
                # dataframe_row = (len(final_dataframe.columns)) * [""]
                # next_row_index = row_index + 1

                # if paragraph.paragraph_format.left_indent == 36830 and "\t" in paragraph.text:
                dataframe_row = parse_paragraph_in_middle_column_to_dataframe(
                    paragraph=paragraph, dataframe_row=dataframe_row
                )

            elif paragraph.paragraph_format.left_indent == 436245:
                # multi line Beschreibung
                dataframe_row[4] += " " + paragraph.text

            if len(create_new_dataframe_row_indicator_list) > i + 1:
                if create_new_dataframe_row_indicator_list[i + 1]:
                    dataframe.loc[row_index] = dataframe_row
                    dataframe_row = (len(dataframe.columns)) * [""]
                    row_index = row_index + 1
            else:
                dataframe.loc[row_index] = dataframe_row
                row_index = row_index + 1

    else:
        for paragraph in middle_cell.paragraphs:

            if paragraph.paragraph_format.left_indent == 36830 and "\t" in paragraph.text:
                # Beschreibung -> 4 -> 436245
                # 11039 -> 5 -> 1962785
                # 11040 -> 6 -> 2578735
                # 11041 -> 7 -> 3192780

                dataframe_row = parse_paragraph_in_middle_column_to_dataframe(
                    paragraph=paragraph, dataframe_row=dataframe_row
                )

            elif paragraph.paragraph_format.left_indent == 36830 and not "\t" in paragraph.text:
                # multi line Freitext
                dataframe_row[3] += " " + paragraph.text
            elif paragraph.paragraph_format.left_indent == 436245:
                # multi line Beschreibung
                dataframe_row[4] += " " + paragraph.text
            elif paragraph.paragraph_format.left_indent is None:
                parse_paragraph_in_middle_column_to_dataframe(paragraph=paragraph, dataframe_row=dataframe_row)
            else:
                raise NotImplementedError(f"The row with {repr(paragraph.text)} can not be read.")

        dataframe.loc[row_index] = dataframe_row
        row_index = row_index + 1
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
):
    if row_type is RowType.HEADER:
        # continue
        pass

    elif row_type is RowType.SEGMENTNAME:
        write_segment_name_to_dataframe(
            dataframe=dataframe,
            row_index=dataframe_row_index,
            dataframe_row=dataframe_row,
            text_in_row_as_list=row_cell_texts_as_list,
        )
        dataframe_row_index = dataframe_row_index + 1
        # continue

    elif row_type is RowType.SEGMENTGRUPPE:
        write_segmentgruppe_to_dataframe(
            dataframe=dataframe,
            row_index=dataframe_row_index,
            dataframe_row=dataframe_row,
            text_in_row_as_list=row_cell_texts_as_list,
            middle_cell=table.row_cells(row)[index_for_middle_column],
        )
        dataframe_row_index = dataframe_row_index + 1
        # continue

    elif row_type is RowType.SEGMENT:
        write_segment_to_dataframe(
            dataframe=dataframe,
            row_index=dataframe_row_index,
            dataframe_row=dataframe_row,
            text_in_row_as_list=row_cell_texts_as_list,
            middle_cell=table.row_cells(row)[index_for_middle_column],
        )
        dataframe_row_index = dataframe_row_index + 1
        # continue

    elif row_type is RowType.DATENELEMENT:
        dataframe_row_index = write_dataelement_to_dataframe(
            dataframe=dataframe,
            row_index=dataframe_row_index,
            dataframe_row=dataframe_row,
            text_in_row_as_list=row_cell_texts_as_list,
            middle_cell=table.row_cells(row)[index_for_middle_column],
        )
        # continue

    elif row_type is RowType.EMPTY:

        # row_index um eins zurücksetzen
        # actual_df_row_index = actual_df_row_index - 1
        pass

    return dataframe_row_index
