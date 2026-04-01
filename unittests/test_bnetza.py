"""Tests for the pure functions in kohlrahbi.changehistory.bnetza."""

from unittest.mock import MagicMock

import pytest

from kohlrahbi.changehistory.bnetza import (
    clean_filename,
    clean_table_data,
    find_change_history_page,
    normalize_table_columns,
)


class TestCleanFilename:
    def test_removes_pdf_size_mb(self):
        assert clean_filename("Document (pdf / 2.5 MB)") == "Document.pdf"

    def test_removes_pdf_size_kb(self):
        assert clean_filename("Report (pdf / 150 KB)") == "Report.pdf"

    def test_replaces_slashes_and_spaces(self):
        assert clean_filename("My Document/v2") == "My_Document_v2.pdf"

    def test_preserves_existing_pdf_extension(self):
        assert clean_filename("file.pdf") == "file.pdf"

    def test_adds_pdf_extension_if_missing(self):
        assert clean_filename("file") == "file.pdf"

    def test_removes_size_and_adds_extension(self):
        assert clean_filename("AHB UTILMD (pdf / 1 MB)") == "AHB_UTILMD.pdf"


class TestNormalizeTableColumns:
    def test_returns_table_unchanged_if_not_10_columns(self):
        table = [["a", "b", "c", "d", "e", "f"]]
        assert normalize_table_columns(table) == table

    def test_returns_empty_table_unchanged(self):
        assert normalize_table_columns([]) == []

    def test_normalizes_10_columns_to_6(self):
        row = ["ID1", "Ort1", "B1", "B2", "B3", "N1", "N2", "N3", "Grund", "Status"]
        result = normalize_table_columns([row])
        assert len(result) == 1
        assert len(result[0]) == 6
        assert result[0][0] == "ID1"
        assert result[0][1] == "Ort1"
        assert result[0][4] == "Grund"
        assert result[0][5] == "Status"

    def test_merges_bisher_and_neu_columns(self):
        row = ["ID", "Ort", "a", None, "c", "x", None, "z", "Grund", "Status"]
        result = normalize_table_columns([row])
        assert result[0][2] == "a\nc"  # Bisher: cols 2-4, None skipped
        assert result[0][3] == "x\nz"  # Neu: cols 5-7, None skipped


class TestCleanTableData:
    def test_returns_empty_for_insufficient_rows(self):
        assert clean_table_data([["header"]]) == []

    def test_preserves_header_and_subheader(self):
        table = [
            ["Änd-ID", "Ort", "Bisher", "Neu", "Grund", "Status"],
            ["", "", "alt", "neu", "", ""],
            ["ID1", "S1", "old", "new", "reason", "done"],
        ]
        result = clean_table_data(table)
        assert result[0] == table[0]  # header
        assert result[1] == table[1]  # sub-header

    def test_merges_continuation_rows(self):
        table = [
            ["Änd-ID", "Ort", "Bisher", "Neu", "Grund", "Status"],
            ["", "", "", "", "", ""],
            ["ID1", "S1", "old", "new", "reason", "done"],
            ["", "", "more old", "", "more reason", ""],
        ]
        result = clean_table_data(table)
        # header + sub-header + 1 merged data row
        assert len(result) == 3
        assert result[2][2] == "old\nmore old"
        assert result[2][4] == "reason\nmore reason"

    def test_converts_none_to_empty_string(self):
        table = [
            ["H1", "H2"],
            ["S1", "S2"],
            ["A", None],
        ]
        result = clean_table_data(table)
        assert result[2] == ["A", ""]


class TestFindChangeHistoryPage:
    def _make_pdf(self, pages_text: list[str]) -> MagicMock:
        """Create a mock PDF with pages returning the given texts."""
        pdf = MagicMock()
        pages = []
        for text in pages_text:
            page = MagicMock()
            page.extract_text.return_value = text
            pages.append(page)
        pdf.pages = pages
        return pdf

    def test_finds_page_from_toc(self):
        pdf = self._make_pdf(
            [
                "Table of Contents\nÄnderungshistorie.....10",
                "Other content",
            ]
        )
        assert find_change_history_page(pdf) == 9  # 10 - 1 = 9 (0-based)

    def test_fallback_finds_page_by_text(self):
        pdf = self._make_pdf(
            [
                "Introduction",
                "Some content",
                "Some content",
                "Some content",
                "Änderungshistorie\nSome changes here",
            ]
        )
        assert find_change_history_page(pdf) == 4

    def test_returns_negative_one_when_not_found(self):
        pdf = self._make_pdf(["No relevant content", "More content"])
        assert find_change_history_page(pdf) == -1

    def test_handles_none_from_extract_text(self):
        pdf = self._make_pdf(["normal text"])
        # Override second page to return None
        none_page = MagicMock()
        none_page.extract_text.return_value = None
        pdf.pages = [pdf.pages[0], none_page]
        # Should not raise TypeError
        assert find_change_history_page(pdf) == -1
