import json
from pathlib import Path
from typing import Union
from uuid import uuid4

import pandas as pd
from maus.edifact import pruefidentifikator_to_format
from maus.models.anwendungshandbuch import (
    AhbLine,
    AhbMetaInformation,
    FlatAnwendungshandbuch,
    FlatAnwendungshandbuchSchema,
)

from kohlrahbi.ahbtable import AhbTable
from kohlrahbi.logger import logger


def convert_ahb_table_to_flatahb(ahb_table: pd.DataFrame, pruefi: str) -> FlatAnwendungshandbuch:
    """
    This function converts a given ahb table into a FlatAnwendungshandbuch
    """

    ahb_lines: list[AhbLine] = []
    index = 0

    for _, row in ahb_table.iterrows():

        if row["Segment Gruppe"].startswith("SG"):

            ahb_lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=row["Segment Gruppe"] or None,
                    segment_code=row["Segment"] or None,
                    data_element=row["Datenelement"] or None,
                    value_pool_entry=row["Codes und Qualifier"] or None,
                    name=row["Beschreibung"] or None,
                    ahb_expression=row[pruefi] or None,
                    section_name=None,
                    index=index,
                )
            )
        else:
            # e.g. Nachrichten-Kopfsegment
            ahb_lines.append(
                AhbLine(
                    guid=uuid4(),
                    segment_group_key=None,
                    segment_code=row["Segment"] or None,
                    data_element=row["Datenelement"] or None,
                    value_pool_entry=row["Codes und Qualifier"] or None,
                    name=row["Beschreibung"] or None,
                    ahb_expression=None,
                    section_name=row["Segment Gruppe"] or None,
                    index=index,
                )
            )
        index = index + 1

    return FlatAnwendungshandbuch(meta=AhbMetaInformation(pruefidentifikator=pruefi), lines=ahb_lines)


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

    with open(flatahb_output_directory_path / f"{pruefi}.json", "w") as f:
        json.dump(dump_data, f)
