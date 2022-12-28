from pathlib import Path
from typing import Union

import pandas as pd
from maus.edifact import pruefidentifikator_to_format

from kohlrahbi.ahbtable import AhbTable
from kohlrahbi.logger import logger


def dump_kohlrahbi_to_csv(kohlrahbi: pd.DataFrame, pruefi: str, output_directory_path: Path):

    edifact_format = pruefidentifikator_to_format(pruefi)
    if edifact_format is None:
        logger.warning("'%s' is not a pruefidentifikator", pruefi)
        return

    csv_output_directory_path = output_directory_path / "csv" / str(edifact_format)

    csv_output_directory_path.mkdir(parents=True, exist_ok=True)

    AhbTable.fill_segement_gruppe_segement_dataelement(df=kohlrahbi)

    # write for each pruefi an extra file
    columns_to_export = list(kohlrahbi.columns)[:5] + [pruefi]
    columns_to_export.append("Bedingung")
    df_to_export = kohlrahbi[columns_to_export]

    df_to_export.to_csv(csv_output_directory_path / f"{pruefi}.csv")
