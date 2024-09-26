from unittest.mock import MagicMock

import pytest

from kohlrahbi.qualitymap import is_quality_map_table


class MockCell:
    def __init__(self, text):
        self.text = text

    def strip(self):
        return self.text.strip()


class MockTable:
    def __init__(self, cell_text):
        self.cell_text = cell_text

    def cell(self, row_idx, col_idx):
        if row_idx == 0 and col_idx == 0:
            return MockCell(self.cell_text)
        raise IndexError


class TestQualityMap:

    def test_is_quality_map_table_true(self):
        table = MockTable("Qualität\n\nSegmentgruppe")
        assert is_quality_map_table(table) is True

    def test_is_quality_map_table_false(self):
        table = MockTable("Some other text")
        assert is_quality_map_table(table) is False

    def test_is_quality_map_table_index_error(self):
        table = MockTable(None)
        table.cell = MagicMock(side_effect=IndexError)
        assert is_quality_map_table(table) is False
