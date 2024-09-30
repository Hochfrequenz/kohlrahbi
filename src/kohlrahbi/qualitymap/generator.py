"""
Contains logic to generate code from the quality map (data model).
"""

import itertools
import re
from dataclasses import replace

from pydantic import BaseModel

from kohlrahbi.qualitymap.qualitymaptable import HEADERS, QualityMapTable


class CellOutput(BaseModel):
    """
    Represents the output of a cell.
    """

    qualifier: str
    description: str
    enum_value: str


def replace_umlauts(description: str) -> str:
    """
    Replace umlauts in the description.
    """
    escape_map = {
        "Ü": "UE",
        "Ä": "AE",
        "Ö": "OE",
        "ß": "ss",
    }
    regex_uppercase = re.compile(r"[ÄÖÜ](?![a-z])")
    regex_capitalize = re.compile(r"[ÄÖÜ](?=[a-z])")
    regex_lowercase = re.compile(r"[äöüß]")
    description = regex_uppercase.sub(lambda x: escape_map[x.group()], description)
    description = regex_capitalize.sub(lambda x: escape_map[x.group()].capitalize(), description)
    description = regex_lowercase.sub(lambda x: escape_map[x.group().upper()].lower(), description)
    return description


def rename_qualifier(qualifier: str, description: str) -> str:
    """
    Rename the qualifier to a valid Python variable name.
    """
    first_three_words = replace_umlauts(description).split()
    return f"{qualifier}_{'_'.join(first_three_words).replace('-', '_')}"


HEADER_TO_ENUM_VALUES = {
    "gueltige_daten": "null",
    "informative_daten": "BO4E.ENUM.Qualitaet.INFORMATIV",
    "erwartete_daten": "BO4E.ENUM.Qualitaet.ERWARTET",
    "im_system_vorhandene_daten": "BO4E.ENUM.Qualitaet.IM_SYSTEM_VORHANDEN",
}


def enum_value(column_attr: str) -> str:
    """
    Get the enum value for a header.
    """
    return HEADER_TO_ENUM_VALUES[column_attr]


def preprocess_table(table: QualityMapTable) -> dict[str, list[CellOutput]]:
    """
    Generate code from the quality map table.
    """
    cell_dict: dict[str, list[CellOutput]] = {}
    for row in table.rows:
        for header in HEADERS:
            if header == "segment_group":
                continue
            if header == "bestellte_daten":
                # They will be ignored for now. Ask Joscha if you wonder why :P
                continue
            for cell in getattr(row, header):
                if cell.qualifier not in cell_dict:
                    cell_dict[cell.qualifier] = []
                    cell_dict[cell.qualifier].append(
                        CellOutput(
                            qualifier=cell.qualifier, description=cell.description, enum_value=enum_value(header)
                        )
                    )
                else:
                    if len(cell_dict[cell.qualifier]) == 1:
                        cell_to_rename = cell_dict[cell.qualifier][0]
                        cell_to_rename.qualifier = rename_qualifier(
                            cell_to_rename.qualifier, cell_to_rename.description
                        )
                    renamed_qualifier = rename_qualifier(cell.qualifier, cell.description)
                    assert not any(
                        renamed_qualifier == cell_output.qualifier for cell_output in cell_dict[cell.qualifier]
                    ), (
                        f"Duplicate qualifier: {renamed_qualifier} "
                        f"in column {header}, row {row.segment_group.path_to_data_element}"
                    )
                    cell_dict[cell.qualifier].append(
                        CellOutput(
                            qualifier=renamed_qualifier, description=cell.description, enum_value=enum_value(header)
                        )
                    )
    return cell_dict


def generate_code(table: QualityMapTable) -> str:
    """
    Generate code from the quality map table.
    """
    cell_dict = preprocess_table(table)
    code = ""
    for cell in itertools.chain(*cell_dict.values()):
        code += f'[Bo4e(typeof(BO4E.ENUM.Qualitaet), {cell.enum_value}, mappingHint: "{cell.description}")]\n'
        code += f"{cell.qualifier},\n\n"
    return code
