"""
This module collects all Prüfidentifikatoren from the AHB documents.
You have to define a path where all AHB docx files are.
"""
from datetime import date
from pathlib import Path

import docx  # type:ignore[import]
import tomlkit
from docx.table import Table  # type:ignore[import]
from maus.edifact import EdifactFormat

from kohlrahbi.harvester import get_all_ahb_docx_files
from kohlrahbi.helper.read_functions import does_the_table_contain_pruefidentifikatoren, get_all_paragraphs_and_tables
from kohlrahbi.helper.seed import Seed
from kohlrahbi.logger import logger

all_pruefis: list[str] = []

for edifact_format in EdifactFormat:
    path_to_ahb_documents: Path = Path("/Users/kevin/workspaces/hochfrequenz/edi_energy_mirror/edi_energy_de/current")

    docx_files_in_ahb_documents = get_all_ahb_docx_files(path_to_ahb_documents=path_to_ahb_documents)

    for ahb_file_path in docx_files_in_ahb_documents:
        doc = docx.Document(ahb_file_path)  # Creating word reader object.

        for item in get_all_paragraphs_and_tables(parent=doc):
            if isinstance(item, Table) and does_the_table_contain_pruefidentifikatoren(table=item):
                # check which pruefis
                seed = Seed.from_table(docx_table=item)
                logger.info("Found a table with the following pruefis: %s", seed.pruefidentifikatoren)
                all_pruefis = all_pruefis + seed.pruefidentifikatoren

all_pruefis = sorted(list(set(all_pruefis)))

toml_data = {
    "meta_data": {"updated_on": date.today()},
    "content": {"pruefidentifikatoren": all_pruefis},
}

with open(Path(__file__).parent / Path("all_known_pruefis.toml"), "w", encoding="utf-8") as f:
    # tomllib does not provide a dump method at the moment
    # https://docs.python.org/uk/dev/library/tomllib.html
    tomlkit.dump(toml_data, f)
