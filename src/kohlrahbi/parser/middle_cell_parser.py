from typing import List
from typing import Callable, Iterable, List, TypeVar

import pandas as pd  # type:ignore[import]
from docx.table import _Cell  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]

T = TypeVar("T")
X = TypeVar("X")


def count_matching(condition: Callable[[T, X], bool], condition_argument: X, seq: Iterable[T]):
    """Returns the amount of items in seq that return true from condition"""
    return sum(condition(item, condition_argument) for item in seq)


def code_condition(paragraph: Paragraph, pruefi_tabstops: List[int]) -> bool:
    """Checks if the paragraph contains a Code by checking for bold style.

    Example for Codes: UTILMD, 11A, UN,


    Args:
        paragraph (Paragraph): Current paragraph
        pruefi_tabstops (List[int]): All tabstop positions of the indicator middle cell

    Returns:
        [bool]:
    """
    try:
        # pylint: disable=protected-access
        tabstop_positions = [tab_position.pos for tab_position in paragraph.paragraph_format.tab_stops._pPr.tabs]
    except TypeError:
        return False

    if paragraph.runs[0].bold is True and any(x in tabstop_positions for x in pruefi_tabstops):
        return True
    return False


def has_middle_cell_multiple_codes(paragraphs: List[Paragraph], pruefi_tabstops: List[int]) -> bool:
    """Checks if the paragraphs of a middle cell contains more than one Code.

    Args:
        paragraphs (List[Paragraph]): All paragraphs in the current middle cell
        pruefi_tabstops (List[int]): All tabstop positions of the indicator middle cell

    Returns:
        bool:
    """

    if count_matching(condition=code_condition, condition_argument=pruefi_tabstops, seq=paragraphs) > 1:
        return True
    return False


def does_paragraph_contain_qualifier_or_code(paragraph, left_indent_position) -> bool:
    if paragraph.paragraph_format.left_indent == left_indent_position:
        return True
    else:
        return False


def parse_middle_paragraph(paragraph, dataframe, row_index, left_indent_position, tabstop_positions):
    splitted_text_at_tabs = paragraph.text.split("\t")

    # Qualifier / Code
    # left_indent_position is characteristic for Datenelemente
    if paragraph.paragraph_format.left_indent == left_indent_position:
        dataframe.at[row_index, "Codes und Qualifier"] += splitted_text_at_tabs.pop(0)
        column_indezes = list(range(4, 4 + len(tabstop_positions)))

    else:
        if splitted_text_at_tabs[0] == "":
            tabstop_positions = tabstop_positions[1:]
            del splitted_text_at_tabs[0]

        column_indezes = list(range(5, 5 + len(tabstop_positions)))

    # pylint: disable=protected-access
    tab_stops = paragraph.paragraph_format.tab_stops._pPr.tabs

    if tab_stops is not None:
        for tabstop in tab_stops:
            for tabstop_position, column_index in zip(tabstop_positions, column_indezes):
                if tabstop.pos == tabstop_position:
                    dataframe.iat[row_index, column_index] += splitted_text_at_tabs.pop(0)
    elif tab_stops is None and splitted_text_at_tabs:
        # in splitted_text_at_tabs list must be an entry
        dataframe.at[row_index, "Beschreibung"] += splitted_text_at_tabs.pop(0)
    elif tab_stops is None:
        pass
    # Could not figure out a scenario where this error could be raised.
    # else:
    #     raise NotImplementedError(f"Could not parse paragraph in middle cell with {paragraph.text}")


def parse_middle_cell(
    table_cell: _Cell,
    # paragraph: Paragraph,
    dataframe: pd.DataFrame,
    row_index: int,
    left_indent_position: int,
    tabstop_positions: List[int],
) -> None:
    """Parses a paragraph in the middle column and puts the information into the appropriate columns

    Args:
        paragraph (Paragraph): Current paragraph in the edifact struktur cell
        dataframe (pd.DataFrame): Contains all infos
        row_index (int): Current index of the DataFrame
        left_indent_position (int): Position of the left indent from the indicator middle cell
        tabstop_positions (List[int]): All tabstop positions of the indicator middle cell
    """

    is_first_iteration = True

    for paragraph in table_cell.paragraphs:

        row_index = dataframe.index.max()

        splitted_text_at_tabs = paragraph.text.split("\t")

        if does_paragraph_contain_qualifier_or_code(paragraph=paragraph, left_indent_position=left_indent_position):

            if not is_first_iteration:
                # a new code and it is not the first. So we add a new row in dataframe and increase the row_index
                dataframe.loc[dataframe.index.max() + 1, :] = ""
                row_index = row_index + 1

            dataframe.at[row_index, "Codes und Qualifier"] += splitted_text_at_tabs.pop(0)
            column_indezes = list(range(4, 4 + len(tabstop_positions)))

        else:
            if splitted_text_at_tabs[0] == "":
                tabstop_positions = tabstop_positions[1:]
                del splitted_text_at_tabs[0]
            column_indezes = list(range(5, 5 + len(tabstop_positions)))

        tab_stops = paragraph.paragraph_format.tab_stops._pPr.tabs

        if tab_stops is not None:
            for tabstop in tab_stops:
                for tabstop_position, column_index in zip(tabstop_positions, column_indezes):
                    if tabstop.pos == tabstop_position:
                        dataframe.iat[row_index, column_index] += splitted_text_at_tabs.pop(0)
        elif tab_stops is None and splitted_text_at_tabs:
            # in splitted_text_at_tabs list must be an entry
            dataframe.at[row_index, "Beschreibung"] += splitted_text_at_tabs.pop(0)
        elif tab_stops is None:
            pass
        # Could not figure out a scenario where this error could be raised.
        # else:
        #     raise NotImplementedError(f"Could not parse paragraph in middle cell with {paragraph.text}")

        # recognize that the first loop is over
        is_first_iteration = False

    # if not has_middle_cell_multiple_codes(paragraphs=table_cell.paragraphs, pruefi_tabstops=tabstop_positions[1:]):

    #     for paragraph in table_cell.paragraphs:
    #         parse_middle_paragraph(
    #             paragraph=paragraph,
    #             dataframe=dataframe,
    #             row_index=row_index,
    #             left_indent_position=left_indent_position,
    #             tabstop_positions=tabstop_positions,
    #         )

    # else:

    #     def create_new_code_indicator_list(table_cell: _Cell) -> List[bool]:
    #         """
    #         If a table cell contains multiple codes we have to
    #         """
    #         return [paragraph.runs[0].bold is True for paragraph in table_cell.paragraphs]
