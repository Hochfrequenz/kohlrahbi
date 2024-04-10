from pathlib import Path

import docx  # type: ignore[import-untyped]
import pandas as pd
from maus.edifact import EdifactFormat

from kohlrahbi.pruefis import get_or_cache_document

# class TestPackageTable:
# def test_from_docx_table(self):
#     path_to_document_mapping: dict[Path, docx.Document] = {}
#     input_path = Path.cwd() / Path(
#         "test-files/docx_files/PARTINAHB-informatorischeLesefassung1.0aKonsolidierteLesefassungmitFehlerkorrekturenStand15.08.2022_20230331_20221001.docx"
#     )
#     doc = get_or_cache_document(input_path, path_to_document_mapping)
#     package_table = get_package_table(document=doc)
#     expected_path = Path.cwd() / Path(
#         "dataframes/PARTINAHB-informatorischeLesefassung1.0aKonsolidierteLesefassungmitFehlerkorrekturenStand15.08.2022_20230331_20221001.json"
#     )
#     with open(expected_path, "r") as file:
#         expected = pd.read_json(file)

#     pd.testing.assert_frame_equal(expected, package_table.table)

# def test_collect_conditions(self):
#     path_to_document_mapping: dict[Path, docx.Document] = {}
#     input_path = Path.cwd() / Path(
#         "test-files/docx_files/PARTINAHB-informatorischeLesefassung1.0aKonsolidierteLesefassungmitFehlerkorrekturenStand15.08.2022_20230331_20221001.docx"
#     )
#     doc = get_or_cache_document(input_path, path_to_document_mapping)
#     package_table = get_package_table(document=doc)
#     actual = {}
#     package_table.collect_conditions(actual, edifact_format=EdifactFormat.PARTIN)
#     assert "PARTIN" in actual
#     assert "15" in actual["PARTIN"].keys()
#     assert "Wenn SG4 NAD+DDM (Netzbetreiber) DE3207 der Code „DE“ nicht vorhanden ist" == actual["PARTIN"]["15"]
