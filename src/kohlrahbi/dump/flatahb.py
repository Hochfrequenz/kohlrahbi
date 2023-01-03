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
from more_itertools import peekable

from kohlrahbi.ahbtable import AhbTable
from kohlrahbi.logger import logger

_segment_group_pattern = re.compile(r"^SG\d+$")


def get_section_name(segment_gruppe_or_section_name: str, last_section_name: str) -> str:
    if not (segment_gruppe_or_section_name.startswith("SG") or segment_gruppe_or_section_name == ""):
        return segment_gruppe_or_section_name
    return last_section_name


def convert_ahb_table_to_flatahb(ahb_table: pd.DataFrame, pruefi: str) -> FlatAnwendungshandbuch:
    """
    This function converts a given ahb table into a FlatAnwendungshandbuch
    """

    ahb_lines: list[AhbLine] = []
    index = 0
    current_section_name: str = ""

    # ahb_table.to_dict(orient="index")

    iterable_ahb_table = peekable(ahb_table.iterrows())

    for _, row in iterable_ahb_table:

        current_section_name = get_section_name(
            segment_gruppe_or_section_name=row["Segment Gruppe"], last_section_name=current_section_name
        )

        if row["Segment Gruppe"].startswith("SG"):
            # e.g. SG2

            ahb_lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=row["Segment Gruppe"] or None,
                    segment_code=row["Segment"] or None,
                    data_element=row["Datenelement"] or None,
                    value_pool_entry=row["Codes und Qualifier"] or None,
                    name=row["Beschreibung"] or None,
                    ahb_expression=row[pruefi] or None,
                    section_name=current_section_name,
                    index=index,
                )
            )
        else:
            # e.g. Nachrichten-Kopfsegment

            try:
                # this try-except catches the case in the last iteration. The peek() method will fail there, because of the iteration end.
                _, next_row = iterable_ahb_table.peek()

                if _segment_group_pattern.match(next_row["Segment Gruppe"]):
                    current_segment_group_key = next_row["Segment Gruppe"]
                else:
                    current_segment_group_key = None
            except StopIteration:
                current_segment_group_key = row["Segment Gruppe"]

            ahb_lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=current_segment_group_key or None,
                    segment_code=row["Segment"] or None,
                    data_element=row["Datenelement"] or None,
                    value_pool_entry=row["Codes und Qualifier"] or None,
                    name=row["Beschreibung"] or None,
                    ahb_expression=None,
                    section_name=current_section_name,
                    index=index,
                )
            )
        index = index + 1

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
