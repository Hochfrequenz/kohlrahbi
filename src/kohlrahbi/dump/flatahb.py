import json
import re
from pathlib import Path
from typing import Union
from uuid import uuid4

import maus
import pandas as pd
from maus.edifact import pruefidentifikator_to_format
from maus.models.anwendungshandbuch import (
    AhbLine,
    AhbMetaInformation,
    FlatAnwendungshandbuch,
    FlatAnwendungshandbuchSchema,
)
from maus.reader.flat_ahb_reader import FlatAhbCsvReader
from more_itertools import peekable

from kohlrahbi.ahbtable import AhbTable
from kohlrahbi.logger import logger

_segment_group_pattern = re.compile(r"^SG\d+$")


def get_section_name(segment_gruppe_or_section_name: str, last_section_name: str) -> str:
    if not (segment_gruppe_or_section_name.startswith("SG") or segment_gruppe_or_section_name == ""):
        return segment_gruppe_or_section_name
    return last_section_name


def is_section_name(ahb_row: pd.Series) -> bool:
    keys_that_must_no_hold_any_values: set[str] = {
        "Segment",
        "Datenelement",
        "Codes und Qualifier",
        "Beschreibung",
        "Bedingung",
    }

    for row_key in keys_that_must_no_hold_any_values:
        if ahb_row[row_key]:
            return False
    return True


def is_segment_group(ahb_row: pd.Series) -> bool:

    if _segment_group_pattern.match(ahb_row["Segment Gruppe"]) and not ahb_row["Segment"]:
        return True
    return False


def is_segment_opening_line(ahb_row: pd.Series) -> bool:

    if ahb_row["Segment"] and not ahb_row["Datenelement"]:
        return True
    return False


def is_just_segment(ahb_row: pd.Series) -> bool:

    if _segment_group_pattern.match(ahb_row["Segment Gruppe"]) and ahb_row["Segment"] and not ahb_row["Datenelement"]:
        return True
    return False


def is_dataelement(ahb_row: pd.Series) -> bool:
    if ahb_row["Datenelement"]:
        return True
    return False


def convert_ahb_table_to_flatahb(ahb_table: pd.DataFrame, pruefi: str) -> FlatAnwendungshandbuch:
    """
    This function converts a given ahb table into a FlatAnwendungshandbuch
    """

    ahb_lines: list[AhbLine] = []
    index = 0
    current_section_name: str = ""

    iterable_ahb_table = peekable(ahb_table.iterrows())

    for _, row in iterable_ahb_table:

        current_section_name = get_section_name(
            segment_gruppe_or_section_name=row["Segment Gruppe"], last_section_name=current_section_name
        )

        if is_section_name(ahb_row=row):
            _, next_row = iterable_ahb_table.peek()
            ahb_expression = next_row[pruefi]

            if _segment_group_pattern.match(next_row["Segment Gruppe"]):
                segment_group_key = next_row["Segment Gruppe"]
            else:
                segment_group_key = None

            ahb_lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=segment_group_key,
                    segment_code=None,
                    data_element=None,
                    value_pool_entry=None,
                    name=None,
                    ahb_expression=ahb_expression or None,
                    section_name=current_section_name,
                    index=index,
                )
            )
            index = index + 1
            continue

        if is_segment_group(ahb_row=row):
            value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
                row["Codes und Qualifier"], row["Beschreibung"]
            )
            ahb_lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=row["Segment Gruppe"] or None,
                    segment_code=row["Segment"] or None,
                    data_element=row["Datenelement"] or None,
                    value_pool_entry=value_pool_entry,
                    name=description,
                    ahb_expression=row[pruefi] or None,
                    section_name=current_section_name,
                    index=index,
                )
            )

        if is_segment_opening_line(ahb_row=row):
            ahb_lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=row["Segment Gruppe"] or None,
                    segment_code=row["Segment"] or None,
                    data_element=None,
                    value_pool_entry=None,
                    name=None,
                    ahb_expression=row[pruefi] or None,
                    section_name=current_section_name,
                    index=index,
                )
            )
            index = index + 1
            continue

        if is_just_segment(ahb_row=row):
            value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
                row["Codes und Qualifier"], row["Beschreibung"]
            )
            ahb_lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=row["Segment Gruppe"] or None,
                    segment_code=row["Segment"] or None,
                    data_element=row["Datenelement"] or None,
                    value_pool_entry=value_pool_entry,
                    name=description,
                    ahb_expression=row[pruefi] or None,
                    section_name=current_section_name,
                    index=index,
                )
            )
            index = index + 1
            continue

        if is_dataelement(ahb_row=row):
            value_pool_entry, description = FlatAhbCsvReader.separate_value_pool_entry_and_name(
                row["Codes und Qualifier"], row["Beschreibung"]
            )

            if _segment_group_pattern.match(row["Segment Gruppe"]):
                segment_group_key = row["Segment Gruppe"]
            else:
                segment_group_key = None

            ahb_lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=segment_group_key,
                    segment_code=row["Segment"] or None,
                    data_element=row["Datenelement"] or None,
                    value_pool_entry=value_pool_entry,
                    name=description,
                    ahb_expression=row[pruefi] or None,
                    section_name=current_section_name,
                    index=index,
                )
            )
            index = index + 1
            continue

    ahb_meta_information: AhbMetaInformation = AhbMetaInformation(pruefidentifikator=pruefi)

    return FlatAnwendungshandbuch(meta=ahb_meta_information, lines=ahb_lines)


def dump_kohlrahbi_to_flatahb(kohlrahbi: pd.DataFrame, pruefi: str, output_directory_path: Path):

    edifact_format = pruefidentifikator_to_format(pruefi)
    if edifact_format is None:
        logger.warning("'%s' is not a pruefidentifikator", pruefi)
        return

    flatahb_output_directory_path = output_directory_path / "flatahb" / str(edifact_format)

    flatahb_output_directory_path.mkdir(parents=True, exist_ok=True)

    AhbTable.fill_segement_gruppe_segement_dataelement(df=kohlrahbi)

    # write for each pruefi an extra file
    columns_to_export = list(kohlrahbi.columns)[:5] + [pruefi]
    columns_to_export.append("Bedingung")
    df_to_export = kohlrahbi[columns_to_export]

    flat_ahb: FlatAnwendungshandbuch = convert_ahb_table_to_flatahb(ahb_table=df_to_export, pruefi=pruefi)

    dump_data = FlatAnwendungshandbuchSchema().dump(flat_ahb)

    with open(flatahb_output_directory_path / f"{pruefi}.json", "w", encoding="utf-8") as f:
        json.dump(dump_data, f)
