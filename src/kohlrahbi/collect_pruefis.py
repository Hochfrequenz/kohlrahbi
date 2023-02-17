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

from kohlrahbi.ahbfilefinder import AhbFileFinder
from kohlrahbi.logger import logger
from kohlrahbi.read_functions import does_the_table_contain_pruefidentifikatoren, get_all_paragraphs_and_tables
from kohlrahbi.seed import Seed

all_pruefis: list[str] = []

# You have to clone the edi_energy_mirror repository and define the path to the current folder.
# https://github.com/Hochfrequenz/edi_energy_mirror
# Just put it next to the kohlrahbi repository.
path_to_ahb_documents: Path = Path.cwd().parent / Path("edi_energy_mirror/edi_energy_de/current")

for edifact_format in EdifactFormat:
    ahb_file_finder = AhbFileFinder.from_input_path(input_path=path_to_ahb_documents)

    ahb_file_finder.filter_for_latest_ahb_docx_files()

    for ahb_file_path in ahb_file_finder.paths_to_docx_files:
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
