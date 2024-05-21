"""
tests all the features the kohlrahbi package provides to process Docx files (by using the docx package)
"""

from pathlib import Path
from typing import Generator

import pytest
from _pytest.fixtures import SubRequest  # type:ignore[import]
from docx import Document
from docx.document import Document as DocumentClass
from docx.table import Table
from docx.text.paragraph import Paragraph

from kohlrahbi.docxfilefinder import DocxFileFinder
from kohlrahbi.read_functions import get_all_paragraphs_and_tables


class TestDocxExtensions:
    @pytest.fixture
    def create_docx_from_filename(self, request: SubRequest, datafiles) -> Generator[DocumentClass, None, None]:
        """a fixture to quickly instantiate a docx.Document from a given docx file name"""
        docx_file_name = request.param
        docx_file_path = datafiles / docx_file_name
        document = Document(docx_file_path)
        yield document

    @pytest.mark.parametrize(
        "create_docx_from_filename",
        [
            pytest.param(
                "UTILMDAHBWiM-informatorischeLesefassung3.1eKonsolidierteLesefassungmitFehlerkorrekturenStand25.10.2022_20230930_20221025.docx",
            )
        ],
        indirect=True,
    )
    @pytest.mark.parametrize("expected_length", [pytest.param(1210)])
    @pytest.mark.datafiles(
        "unittests/test-edi-energy-mirror-repo/docx_files/UTILMDAHBWiM-informatorischeLesefassung3.1eKonsolidierteLesefassungmitFehlerkorrekturenStand25.10.2022_20230930_20221025.docx"
    )
    def test_get_all_paragraphs_and_tables(self, create_docx_from_filename: DocumentClass, expected_length: int):
        actual = list(get_all_paragraphs_and_tables(create_docx_from_filename))
        assert len(actual) == expected_length
        assert all([isinstance(x, Table) or isinstance(x, Paragraph) for x in actual]) is True

    @pytest.mark.parametrize(
        "all_file_paths, filtered_file_paths",
        [
            pytest.param(
                [Path("IFTSTAAHB-informatorischeLesefassung2.0e_99991231_20231001.docx")],
                [Path("IFTSTAAHB-informatorischeLesefassung2.0e_99991231_20231001.docx")],
                id="One file",
            ),
            pytest.param(
                [
                    Path("IFTSTAAHB-informatorischeLesefassung2.0e_99991231_20231001.docx"),
                    Path(
                        "IFTSTAAHB-informatorischeLesefassung2.0e-AußerordentlicheVeröffentlichung_20231211_20231001.docx"
                    ),
                    Path(
                        "IFTSTAAHB-informatorischeLesefassung2.0eKonsolidierteLesefassungmitFehlerkorrekturenStand11.03.2024_99991231_20240311.docx"
                    ),
                    Path(
                        "IFTSTAAHB-informatorischeLesefassung2.0eKonsolidierteLesefassungmitFehlerkorrekturenStand12.12.2023_20240310_20231212.docx"
                    ),
                ],
                [
                    Path(
                        "IFTSTAAHB-informatorischeLesefassung2.0eKonsolidierteLesefassungmitFehlerkorrekturenStand11.03.2024_99991231_20240311.docx"
                    )
                ],
                id="Several files",
            ),
        ],
    )
    def test_filter_lastest_version(self, all_file_paths, filtered_file_paths):
        input_file_dict = {"FORMAT": all_file_paths}
        actual = DocxFileFinder.filter_latest_version(input_file_dict)
        assert actual == filtered_file_paths
