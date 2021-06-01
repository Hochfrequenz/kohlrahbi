from pathlib import Path
from typing import List

import docx
import numpy as np
import pandas as pd

directory_path = Path.cwd() / "documents"
file_name = "UTILMD_AHB_WiM_3_1c_2021_04_01_2021_03_30.docx"

path_to_file = directory_path / file_name


def main():
    try:
        doc = docx.Document(path_to_file)  # Creating word reader object.

        # TODO for each section get header to get prüfidentifaktoren for dataframe header

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
            ]
        )

        df_row_index: int = 0
        # for table in doc.tables[2 : len(doc.tables)]:
        for table in doc.tables[1:20]:

            # table = doc.tables[i]

            for row in range(len(table.rows)):

                # dataframe_row = (len(df.columns)) * [np.nan]
                dataframe_row = (len(df.columns)) * [""]

                # skip table header
                if table.row_cells(row)[0].text == "EDIFACT Struktur":
                    continue

                # distinguish between 4 and 3 column tables
                if len(table.row_cells(row)) == 4:

                    # for cell in table.row_cells(row):

                    # breakpoint

                    row_cells_as_list = [cell.text for cell in table.row_cells(row)]

                    # Write segment name like "Nachrichten-Kopfsegment"
                    if (
                        row_cells_as_list[0]
                        and not row_cells_as_list[1]
                        and not row_cells_as_list[2]
                        and not row_cells_as_list[3]
                    ):
                        dataframe_row[0] = row_cells_as_list[0]
                        df.loc[df_row_index] = dataframe_row
                        df_row_index = df_row_index + 1
                        continue

                    # for cell in table.row_cells(row):
                    # middle column is double in four column tables -> skip one column
                    for column_number in [0, 1, 3]:
                        cell = table.row_cells(row)[column_number]

                        # at this left_indent, there is now Segment-Gruppe
                        if column_number == 0 and cell.paragraphs[0].paragraph_format.left_indent == 364490:
                            # Segement and Datenelement in cell, example: "UNH\t0062"
                            if "\t" in cell.text:
                                splitted_edifact_struktur_column: List = cell.text.split("\t")
                                print(splitted_edifact_struktur_column)
                                # TODO if someone knows a better way, suggestions are very welcome =)
                                dataframe_row[1], dataframe_row[2] = (
                                    splitted_edifact_struktur_column[0],
                                    splitted_edifact_struktur_column[1],
                                )
                                continue
                            # only Segement in cell, example: "UNH"
                            else:
                                dataframe_row[1] = cell.text
                                continue

                        if column_number == 1:
                            # check if cell is in Segment level
                            if cell.paragraphs[0].paragraph_format.left_indent is None:
                                splitted_text = cell.text.split("\t")
                                dataframe_row[5], dataframe_row[6], dataframe_row[7] = (
                                    splitted_text[1],
                                    splitted_text[2],
                                    splitted_text[3],
                                )

                            # check if cell is in Datenelement level
                            if cell.paragraphs[0].paragraph_format.left_indent == 36830:

                                tabs = cell.paragraphs[0].paragraph_format.tab_stops._pPr.tabs

                                if "\n" in cell.text:

                                    if len(tabs) == 4 and "\t" in cell.text.split("\n")[1]:
                                        splitted_text_at_line_endings: List = cell.text.split("\n")

                                        splitted_text_at_tabs = [
                                            snippet.split("\t") for snippet in splitted_text_at_line_endings
                                        ]

                                        fixed_text = [
                                            text[0] + text[1]
                                            for text in zip(splitted_text_at_tabs[0], splitted_text_at_tabs[1])
                                        ]

                                        dataframe_row[3], dataframe_row[4] = fixed_text[0], fixed_text[1]

                                if len(tabs) == 3:
                                    splitted_text = cell.text.split("\t")
                                    dataframe_row[3], dataframe_row[5], dataframe_row[6], dataframe_row[7] = (
                                        splitted_text[0],
                                        splitted_text[1],
                                        splitted_text[2],
                                        splitted_text[3],
                                    )

                                # Beschreibung -> 4 -> 436245
                                # 11039 -> 5 -> 1962785
                                # 11040 -> 6 -> 2578735
                                # 11041 -> 7 -> 3192780
                                # 'UTILM\tNetzanschluss-\tX\tX\tX\nD\tStammdaten'
                                # split \n check if \t is in second entry

                                print(cell.text)
                                print(cell.paragraphs[0].paragraph_format.left_indent)

                    df.loc[df_row_index] = dataframe_row

                    df_row_index = df_row_index + 1

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

                    print(repr(cell.text))
                    print(cell.paragraphs[0].paragraph_format.left_indent)
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
