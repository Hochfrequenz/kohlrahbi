"""
tests all the features the kohlrahbi package provides to process Docx files (by using the docx package)
"""
import pytest  # type:ignore[import]
from _pytest.fixtures import SubRequest  # type:ignore[import]
from docx import Document  # type:ignore[import]
from docx.document import Document as DocumentClass  # type:ignore[import]
from docx.table import Table  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]

from kohlrahbi.read_functions import get_all_paragraphs_and_tables


class TestDocxExtensions:
    @pytest.fixture
    def create_docx_from_filename(self, request: SubRequest, datafiles) -> DocumentClass:
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
        "unittests/docx_files/UTILMDAHBWiM-informatorischeLesefassung3.1eKonsolidierteLesefassungmitFehlerkorrekturenStand25.10.2022_20230930_20221025.docx"
    )
    def test_get_all_paragraphs_and_tables(self, create_docx_from_filename: DocumentClass, expected_length: int):
        actual = list(get_all_paragraphs_and_tables(create_docx_from_filename))
        assert len(actual) == expected_length
        assert all([isinstance(x, Table) or isinstance(x, Paragraph) for x in actual]) is True
