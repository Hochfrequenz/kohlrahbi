from pathlib import Path
from typing import List

import docx
import pandas as pd

from check_row_type import RowType, define_row_type
from write_functions import (
    write_dataelement_to_dataframe,
    write_segment_name_to_dataframe,
    write_segment_to_dataframe,
    write_segmentgruppe_to_dataframe,
)

directory_path = Path.cwd() / "documents"
file_name = "UTILMD_AHB_WiM_3_1c_2021_04_01_2021_03_30.docx"

path_to_file = directory_path / file_name


def main():
    try:
        doc = docx.Document(path_to_file)  # Creating word reader object.

        # TODO for each section get header to get prüfidentifaktoren for dataframe header

        actual_df_row_index: int = 0

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

        # for table in doc.tables[1 : len(doc.tables)]:
        for table in doc.tables[1:20]:

            for row in range(len(table.rows)):

                index_for_middle_column = 1
                # initial empty list for the next row in the dataframe
                actual_dataframe_row = (len(df.columns)) * [""]

                # idea: cause of double information in 4 column tables, remove entry [2] from row_cell_texts_as_list
                row_cell_texts_as_list = [cell.text for cell in table.row_cells(row)]
                if table._column_count == 4:
                    # remove redundant information for tables with 4 columns
                    if (
                        row_cell_texts_as_list[0] == row_cell_texts_as_list[1]
                        and row_cell_texts_as_list[2] == row_cell_texts_as_list[3]
                    ):
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

                    index_for_middle_column = 2

                actual_edifact_struktur_cell = table.row_cells(row)[0]

                # check here for row type
                actual_row_type = define_row_type(
                    table=table,
                    edifact_struktur_cell=actual_edifact_struktur_cell,
                    text_in_row_as_list=row_cell_texts_as_list,
                )
                print(actual_row_type.name)

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
                        middle_cell=table.row_cells(row)[index_for_middle_column],
                    )
                    actual_df_row_index = actual_df_row_index + 1
                    continue

                elif actual_row_type is row_type.SEGMENT:
                    write_segment_to_dataframe(
                        final_dataframe=df,
                        row_index=actual_df_row_index,
                        dataframe_row=actual_dataframe_row,
                        text_in_row_as_list=row_cell_texts_as_list,
                        middle_cell=table.row_cells(row)[index_for_middle_column],
                    )
                    actual_df_row_index = actual_df_row_index + 1
                    continue

                elif actual_row_type is row_type.DATENELEMENT:
                    actual_df_row_index = write_dataelement_to_dataframe(
                        final_dataframe=df,
                        row_index=actual_df_row_index,
                        dataframe_row=actual_dataframe_row,
                        text_in_row_as_list=row_cell_texts_as_list,
                        middle_cell=table.row_cells(row)[index_for_middle_column],
                    )
                    continue

                elif actual_row_type is row_type.EMPTY:
                    # IDEE: merke immer den letzten row_type

                    # row_index um eins zurücksetzen
                    # actual_df_row_index = actual_df_row_index - 1
                    pass

        df.to_csv("export.csv")
        # df.to_excel("export.xlsx")
        print(len(doc.tables[1].columns))

    except IOError:
        print("There was an error opening the file!")
        return


if __name__ == "__main__":
    main()
