"""
tests all the features the kohlrahbi package provides to process Docx files (by using the docx package)
"""
from pathlib import Path

import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest  # type:ignore[import]
from docx import Document  # type:ignore[import]
from docx.table import Table  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]

from kohlrahbi.helper.read_functions import get_all_paragraphs_and_tables


class TestDocxExtensions:
    @pytest.fixture
    def create_docx_from_filename(self, request: SubRequest, datafiles) -> Document:
        """a fixture to quickly instantiate a docx.Document from a given docx file name"""
        docx_file_name = request.param
        docx_file_path = datafiles / docx_file_name
        document = Document(docx_file_path)
        yield document

    @pytest.mark.parametrize(
        "create_docx_from_filename",
        [pytest.param("UTILMD_AHB_WiM-informatorischeLesefassung_3.1e_99991231_20221001.docx")],
        indirect=True,
    )
    @pytest.mark.parametrize("expected_length", [pytest.param(1218)])
    @pytest.mark.datafiles("unittests/docx_files/UTILMD_AHB_WiM-informatorischeLesefassung_3.1e_99991231_20221001.docx")
    def test_get_all_paragraphs_and_tables(self, create_docx_from_filename: Document, expected_length: int):
        actual = list(get_all_paragraphs_and_tables(create_docx_from_filename))
        assert len(actual) == expected_length
        assert all([isinstance(x, Table) or isinstance(x, Paragraph) for x in actual]) is True

    @pytest.mark.parametrize(
        "create_docx_from_filename",
        [pytest.param("test-dataelement-on-after-page-break.docx")],
        indirect=True,
    )
    @pytest.mark.datafiles("unittests/docx_files/test-dataelement-on-after-page-break.docx")
    def test_write_dataelement_after_page_break(self, create_docx_from_filename: Document):
        get_ahb_extract(
            create_docx_from_filename, output_directory_path=Path.cwd() / "test-output", ahb_file_name="foo.bar"
        )
