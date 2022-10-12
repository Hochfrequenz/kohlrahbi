"""Collections of functions which are needed to export the created DataFrame into a file.

The possible file types are:
    * csv
    * json
    * xlsx

You can save each Prüfidentifikator into a separate file or
save all Prüfidentifikators of one AHB in one Excel file.
"""

import re
from pathlib import Path
from typing import TypeVar

import pandas as pd  # type:ignore[import]

from ahbextractor import logger

T = TypeVar("T")


def beautify_bedingungen(bedingung: T) -> T:
    """Inserts newline characters before each Bedingung key [###]

        Example:
        [12] Wenn SG4
    DTM+471 (Ende zum
    nächstmöglichem
    Termin) nicht vorhanden

    [13] Wenn SG4
    STS+E01++Z01 (Status
    der Antwort: Zustimmung
    mit Terminänderung)
    nicht vorhanden

    ->

    [12] Wenn SG4 DTM+471 (Ende zum nächstmöglichen Termin) nicht vorhanden
    [13] Wenn SG4 STS+E01++Z01 (Status der Antwort: Zustimmung mit Terminänderung) nicht vorhanden

    Args:
        bedingung (str): Text in a Bedingung cell

    Returns:
        str: Beautified text with one Bedingung per line
    """

    if isinstance(bedingung, str):
        bedingung = bedingung.replace("\n", " ")
        matches = re.findall(r"\[\d*\]", bedingung)
        for match in matches[1:]:
            index = bedingung.find(match)
            bedingung = (
                bedingung[:index].strip().replace("  ", " ") + "\n" + bedingung[index:].strip().replace("  ", " ")
            )
    return bedingung


# pylint: disable=too-many-locals
def export_single_pruefidentifikator(pruefi: str, df: pd.DataFrame, output_directory_path: Path) -> None:
    """Exports the current Prüfidentifikator in different file formats: json, csv and xlsx
    Each Prüfidentifikator is saved in an extra file.

    Args:
        pruefi (str): Current Prüfidentifikator
        df (pd.DataFrame): DataFrame which contains all information
        output_directory_path (Path): Path to the output directory
    """

    json_output_directory_path = output_directory_path / "json"
    csv_output_directory_path = output_directory_path / "csv"
    xlsx_output_directory_path = output_directory_path / "xlsx"

    json_output_directory_path.mkdir(parents=True, exist_ok=True)
    csv_output_directory_path.mkdir(parents=True, exist_ok=True)
    xlsx_output_directory_path.mkdir(parents=True, exist_ok=True)

    # write for each pruefi an extra file
    columns_to_export = list(df.columns)[:5] + [pruefi]
    columns_to_export.append("Bedingung")
    # df["Bedingung"] = df["Bedingung"].apply(beautify_bedingungen)
    df_to_export = df[columns_to_export]
    df_to_export.to_csv(csv_output_directory_path / f"{pruefi}.csv")

    df_to_export.to_json(json_output_directory_path / f"{pruefi}.json", force_ascii=False, orient="records")
    excel_file_name = f"{pruefi}.xlsx"
    try:
        # https://github.com/PyCQA/pylint/issues/3060 pylint: disable=abstract-class-instantiated
        with pd.ExcelWriter(xlsx_output_directory_path / excel_file_name, engine="xlsxwriter") as writer:
            df_to_export.to_excel(writer, sheet_name=f"{pruefi}")
            # pylint: disable=no-member
            workbook = writer.book
            worksheet = writer.sheets[f"{pruefi}"]
            wrap_format = workbook.add_format({"text_wrap": True})
            column_letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
            column_widths = [3.5, 47, 9, 14, 39, 33, 18, 102]
            for column_letter, column_width in zip(column_letters, column_widths):
                excel_header = f"{column_letter}:{column_letter}"
                worksheet.set_column(excel_header, column_width, wrap_format)
            logger.info("💾 Saved files for Pruefidentifikator %s", pruefi)
    except PermissionError:
        logger.error("The Excel file %s is open. Please close this file and try again.", excel_file_name)


def export_all_pruefidentifikatoren_in_one_file(
    pruefi: str, df: pd.DataFrame, output_directory_path: Path, file_name: Path
) -> None:
    """Exports all Prüfidentifikatoren in one AHB into **one** Excel file

    Args:
        pruefi (str): Current Prüfidentifikator
        df (pd.DataFrame): DataFrame which contains all information
        output_directory_path (Path): Path to the output directory
        file_name (str): Name of the read AHB file
    """

    xlsx_output_directory_path = output_directory_path / "xlsx"
    xlsx_output_directory_path.mkdir(parents=True, exist_ok=True)

    path_to_all_in_one_excel = xlsx_output_directory_path / f"{str(file_name.parts[-1])[:-5]}.xlsx"

    # write for each pruefi an extra file
    # take the first five column header's names and add the current pruefi
    columns_to_export = list(df.columns)[:5] + [pruefi]
    columns_to_export.append("Bedingung")
    df_to_export = df[columns_to_export]
    excel_file_name = str(file_name)[:-5] + ".xlsx"
    try:
        # https://github.com/PyCQA/pylint/issues/3060 pylint: disable=abstract-class-instantiated
        with pd.ExcelWriter(
            path=path_to_all_in_one_excel, mode="a", engine="openpyxl", if_sheet_exists="replace"
        ) as writer:
            df_to_export.to_excel(writer, sheet_name=f"{pruefi}")
    except FileNotFoundError:
        # https://github.com/PyCQA/pylint/issues/3060 pylint: disable=abstract-class-instantiated
        with pd.ExcelWriter(path=path_to_all_in_one_excel, mode="w", engine="openpyxl") as writer:
            df_to_export.to_excel(writer, sheet_name=f"{pruefi}")
    except PermissionError:
        logger.error("The Excel file %s is open. Please close this file and try again.", excel_file_name)
