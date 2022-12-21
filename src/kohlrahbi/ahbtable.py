import attrs
import pandas as pd
from docx.table import Table  # type:ignore[import]

from kohlrahbi.ahbtablerow import AhbTableRow
from kohlrahbi.helper.row_type_checker import RowType, get_row_type
from kohlrahbi.helper.seed import Seed


@attrs.define(auto_attribs=True, kw_only=True)
class AhbTable:
    seed: Seed
    table: Table

    def parse(self, ahb_table_dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Iterates through all rows of the AhbTable.table and writes all extracted infos in a DataFrame.

        Args:
            ahb_table_dataframe (pd.DataFrame): The dataframe which gets exported at the end.

        Returns:
            pd.DataFrame: Returns the ahb_table_dataframe with the added information.
        """

        # pylint: disable=protected-access
        index_for_body_column = self.define_index_for_body_column()

        for row in range(len(self.table.rows)):

            row_cell_texts_as_list = [cell.text for cell in self.table.row_cells(row)]

            if len(self.table.columns) == 4:
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

            current_edifact_struktur_cell = self.table.row_cells(row)[0]

            # check for row type
            current_row_type = get_row_type(
                edifact_struktur_cell=current_edifact_struktur_cell,
                left_indent_position=self.seed.edifact_struktur_left_indent_position,
            )

            edifact_struktur_cell = self.table.row_cells(row)[0]
            middle_cell = self.table.row_cells(row)[index_for_body_column]
            bedingung_cell = self.table.row_cells(row)[-1]

            # this case covers the "normal" docx table row
            if not (current_row_type is RowType.EMPTY and self.seed.last_two_row_types[0] is RowType.HEADER):

                ahb_table_row = AhbTableRow(
                    seed=self.seed,
                    edifact_struktur_cell=edifact_struktur_cell,
                    middle_cell=middle_cell,
                    bedingung_cell=bedingung_cell,
                )

                ahb_table_row_dataframe = ahb_table_row.parse(row_type=current_row_type)

                if ahb_table_dataframe is not None:
                    ahb_table_dataframe = pd.concat([ahb_table_dataframe, ahb_table_row_dataframe], ignore_index=True)
            # this case covers the page break situation
            else:

                ahb_table_row = AhbTableRow(
                    seed=self.seed,
                    edifact_struktur_cell=edifact_struktur_cell,
                    middle_cell=middle_cell,
                    bedingung_cell=bedingung_cell,
                )

                ahb_table_row.parse(row_type=self.seed.last_two_row_types[1], is_appending=True)

        return ahb_table_dataframe

    def define_index_for_body_column(self) -> int:
        """ """
        if self.table._column_count == 4:
            return 2
        else:
            return 1

    @staticmethod
    def fill_segement_gruppe_segement_dataelement(df: pd.DataFrame):

        latest_segement_gruppe: str = ""
        latest_segement: str = ""
        latest_datenelement: str = ""

        for _, row in df.iterrows():
            if row["Segment Gruppe"] == "" and row["Codes und Qualifier"] != "":
                row["Segment Gruppe"] = latest_segement_gruppe
                row["Segment"] = latest_segement
                row["Datenelement"] = latest_datenelement
            latest_segement_gruppe: str = row["Segment Gruppe"]
            latest_segement: str = row["Segment"]
            latest_datenelement: str = row["Datenelement"]
