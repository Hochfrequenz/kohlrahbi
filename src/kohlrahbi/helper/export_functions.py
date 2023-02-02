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
from typing import Any, TypeVar, overload

import pandas as pd
from maus.edifact import get_format_of_pruefidentifikator

from kohlrahbi.dump.excel import write_excel_file
from kohlrahbi.logger import logger

_T = TypeVar("_T")


@overload
def beautify_bedingungen(bedingung: str) -> str:
    ...


@overload
def beautify_bedingungen(bedingung: _T) -> _T:
    ...


def beautify_bedingungen(bedingung: Any) -> Any:
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
        bedingung_str: str = bedingung
        bedingung_str = bedingung_str.replace("\n", " ")
        matches = re.findall(r"\[\d*\]", bedingung_str)
        for match in matches[1:]:
            index = bedingung_str.find(match)
            bedingung_str = (
                bedingung_str[:index].strip().replace("  ", " ")
                + "\n"
                + bedingung_str[index:].strip().replace("  ", " ")
            )
        return bedingung_str
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

    edifact_format = get_format_of_pruefidentifikator(pruefi)
    if edifact_format is None:
        logger.warning("'%s' is not a pruefidentifikator", pruefi)
        return
    json_output_directory_path = output_directory_path / "json" / str(edifact_format)
    csv_output_directory_path = output_directory_path / "csv" / str(edifact_format)
    xlsx_output_directory_path = output_directory_path / "xlsx" / str(edifact_format)

    json_output_directory_path.mkdir(parents=True, exist_ok=True)
    csv_output_directory_path.mkdir(parents=True, exist_ok=True)
    xlsx_output_directory_path.mkdir(parents=True, exist_ok=True)

    # write for each pruefi an extra file
    columns_to_export = list(df.columns)[:5] + [pruefi]
    columns_to_export.append("Bedingung")
    df_to_export = df[columns_to_export]

    df_to_export.to_csv(csv_output_directory_path / f"{pruefi}.csv")

    df_to_export.to_json(json_output_directory_path / f"{pruefi}.json", force_ascii=False, orient="records")

    write_excel_file(df_to_export=df_to_export, pruefi=pruefi, output_directory_path=output_directory_path)


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
