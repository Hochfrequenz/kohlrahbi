import pytest  # type:ignore[import]
from docx import Document
from maus.edifact import EdifactFormat

from kohlrahbi.read_functions import is_item_package_heading


def create_heading_paragraph(text, style):
    paragraph = Document().add_paragraph(text)
    paragraph.style = style
    return paragraph


class TestReadFunctions:
    @pytest.mark.parametrize(
        "item, style_name, expected_boolean",
        [
            pytest.param(
                create_heading_paragraph("Übersicht der Pakete in der UTILMD", "Heading 1"),
                "Heading 1",
                True,
                id="heading1_valid",
            ),
            pytest.param(
                create_heading_paragraph("Übersicht der Pakete in der UTILMD", "Heading 2"),
                "Heading 2",
                True,
                id="heading2_valid",
            ),
            pytest.param(
                create_heading_paragraph("Übersicht der Pakete in der UTILMD", "Heading 3"),
                "Heading 3",
                False,
                id="invalid_style",
            ),
            pytest.param(
                create_heading_paragraph("Übersicht der Pakete in der IFSTA", "Heading 2"),
                "Heading 2",
                False,
                id="invalid_edifact_format",
            ),
            pytest.param(
                Document().add_table(rows=1, cols=1),
                "Heading 2",
                False,
                id="table_invalid",
            ),
        ],
    )
    def test_is_package_item_heading(self, item, style_name, expected_boolean):
        assert is_item_package_heading(item, style_name, EdifactFormat.UTILMD) == expected_boolean
