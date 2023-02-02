"""
This module contains all functions to export a kohlrahbi to excel file
"""

from pathlib import Path
from typing import Union

import pandas as pd
from maus.edifact import get_format_of_pruefidentifikator

from kohlrahbi.ahbtable import AhbTable
from kohlrahbi.logger import logger

_column_letter_width_mapping: dict[str, Union[float, int]] = {
    "A": 3.5,
    "B": 47,
    "C": 9,
    "D": 14,
    "E": 39,
    "F": 33,
    "G": 18,
    "H": 102,
}


def write_excel_file(df_to_export: pd.DataFrame, pruefi: str, output_directory_path: Path):
    """
    Write your dataframe of the given Prüfidentifikator in the given output directory.
    """
    edifact_format = get_format_of_pruefidentifikator(pruefi)
    xlsx_output_directory_path: Path = output_directory_path / "xlsx" / str(edifact_format)
    xlsx_output_directory_path.mkdir(parents=True, exist_ok=True)

    excel_file_name = f"{pruefi}.xlsx"
    try:
        # https://github.com/PyCQA/pylint/issues/3060 pylint: disable=abstract-class-instantiated
        with pd.ExcelWriter(xlsx_output_directory_path / excel_file_name, engine="xlsxwriter") as writer:
            df_to_export.to_excel(writer, sheet_name=f"{pruefi}")
            # pylint: disable=no-member
            workbook = writer.book
            worksheet = writer.sheets[f"{pruefi}"]
            wrap_format = workbook.add_format({"text_wrap": True})
            for column_letter, column_width in _column_letter_width_mapping.items():
                excel_header = f"{column_letter}:{column_letter}"
                worksheet.set_column(excel_header, column_width, wrap_format)
            logger.info("💾 Saved files for Pruefidentifikator %s", pruefi)
    except PermissionError:
        logger.error("The Excel file %s is open. Please close this file and try again.", excel_file_name)


def extract_one_pruefi_from_ahb_table(df: pd.DataFrame, pruefi: str) -> pd.DataFrame:
    """
    AHB tables often include more than one Prüfidentifikatoren.
    This function creates a table which contains only one Prüfidentifikator at the end.
    """
    columns_to_export = list(df.columns)[:5] + [pruefi]
    columns_to_export.append("Bedingung")

    AhbTable.fill_segement_gruppe_segement_dataelement(df=df)

    return df[columns_to_export]


def dump_kohlrahbi_to_excel(kohlrahbi: pd.DataFrame, pruefi: str, output_directory_path: Path):
    """
    Dump a given kohlrahbi into an excel file
    """

    edifact_format = get_format_of_pruefidentifikator(pruefi)
    if edifact_format is None:
        logger.warning("'%s' is not a pruefidentifikator", pruefi)
        return

    df_to_export = extract_one_pruefi_from_ahb_table(df=kohlrahbi, pruefi=pruefi)

    write_excel_file(df_to_export=df_to_export, pruefi=pruefi, output_directory_path=output_directory_path)
