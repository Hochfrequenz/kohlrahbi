import re

import pandas as pd  # type:ignore[import]
from docx.table import _Cell  # type:ignore[import]


def parse_bedingung_cell(bedingung_cell: _Cell, dataframe: pd.DataFrame) -> None:
    """Parses a cell in the Bedingung column and puts the information into the in the appropriate column of the dataframe

    Args:
        bedingung_cell (_Cell): Cell from the Bedingung column
        dataframe (pd.DataFrame): Saves all infos
    """

    row_index = dataframe.index.max()

    bedingung = bedingung_cell.text.replace("\n", " ")
    matches = re.findall(r"\[\d+\]", bedingung)
    for match in matches[1:]:
        index = bedingung.find(match)
        bedingung = bedingung[:index] + "\n" + bedingung[index:]

    dataframe.at[row_index, "Bedingung"] += bedingung
