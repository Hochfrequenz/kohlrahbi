"""Tests for the pure functions in kohlrahbi.changehistory.bnetza."""

import asyncio
import io
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pandas as pd
import pytest

from kohlrahbi.changehistory import bnetza
from kohlrahbi.changehistory.bnetza import (
    DownloadResult,
    _collect_sheets_data,
    _filename_stem_from_url,
    _is_change_history_header,
    _rows_to_change_history_df,
    _unique_sheet_name,
    clean_filename,
    clean_table_data,
    detect_document_type,
    extract_document_links,
    find_change_history_page,
    normalize_table_columns,
)


class TestCleanFilename:
    def test_removes_pdf_size_mb(self) -> None:
        assert clean_filename("Document (pdf / 2.5 MB)") == "Document.pdf"

    def test_removes_pdf_size_kb(self) -> None:
        assert clean_filename("Report (pdf / 150 KB)") == "Report.pdf"

    def test_replaces_slashes_and_spaces(self) -> None:
        assert clean_filename("My Document/v2") == "My_Document_v2.pdf"

    def test_preserves_existing_pdf_extension(self) -> None:
        assert clean_filename("file.pdf") == "file.pdf"

    def test_adds_pdf_extension_if_missing(self) -> None:
        assert clean_filename("file") == "file.pdf"

    def test_removes_size_and_adds_extension(self) -> None:
        assert clean_filename("AHB UTILMD (pdf / 1 MB)") == "AHB_UTILMD.pdf"


class TestNormalizeTableColumns:
    def test_returns_table_unchanged_if_not_10_columns(self) -> None:
        table: list[list[str | None]] = [["a", "b", "c", "d", "e", "f"]]
        assert normalize_table_columns(table) == table

    def test_returns_empty_table_unchanged(self) -> None:
        assert normalize_table_columns([]) == []

    def test_normalizes_10_columns_to_6(self) -> None:
        row: list[str | None] = ["ID1", "Ort1", "B1", "B2", "B3", "N1", "N2", "N3", "Grund", "Status"]
        result = normalize_table_columns([row])
        assert len(result) == 1
        assert len(result[0]) == 6
        assert result[0][0] == "ID1"
        assert result[0][1] == "Ort1"
        assert result[0][4] == "Grund"
        assert result[0][5] == "Status"

    def test_merges_bisher_and_neu_columns(self) -> None:
        row: list[str | None] = ["ID", "Ort", "a", None, "c", "x", None, "z", "Grund", "Status"]
        result = normalize_table_columns([row])
        assert result[0][2] == "a\nc"  # Bisher: cols 2-4, None skipped
        assert result[0][3] == "x\nz"  # Neu: cols 5-7, None skipped


class TestCleanTableData:
    def test_returns_empty_for_insufficient_rows(self) -> None:
        assert clean_table_data([["header"]]) == []

    def test_preserves_header_and_subheader(self) -> None:
        table: list[list[str | None]] = [
            ["Änd-ID", "Ort", "Bisher", "Neu", "Grund", "Status"],
            ["", "", "alt", "neu", "", ""],
            ["ID1", "S1", "old", "new", "reason", "done"],
        ]
        result = clean_table_data(table)
        assert result[0] == table[0]  # header
        assert result[1] == table[1]  # sub-header

    def test_merges_continuation_rows(self) -> None:
        table: list[list[str | None]] = [
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

    def test_converts_none_to_empty_string(self) -> None:
        table: list[list[str | None]] = [
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

    def test_finds_page_from_toc(self) -> None:
        pdf = self._make_pdf(
            [
                "Table of Contents\nÄnderungshistorie.....10",
                "Other content",
            ]
        )
        assert find_change_history_page(pdf) == 9  # 10 - 1 = 9 (0-based)

    def test_fallback_finds_page_by_text(self) -> None:
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

    def test_returns_negative_one_when_not_found(self) -> None:
        pdf = self._make_pdf(["No relevant content", "More content"])
        assert find_change_history_page(pdf) == -1

    def test_handles_none_from_extract_text(self) -> None:
        pdf = self._make_pdf(["normal text"])
        # Override second page to return None
        none_page = MagicMock()
        none_page.extract_text.return_value = None
        pdf.pages = [pdf.pages[0], none_page]
        # Should not raise TypeError
        assert find_change_history_page(pdf) == -1


# HTML mirroring a modern BNetzA "Mitteilung" page: a <base href="/">, download links that are
# relative *without* a leading slash, a PDF, an .html-named download, an .xlsx, a duplicate link
# and a plain non-download link that must be ignored.
_BNETZA_PAGE_HTML = """
<html><head><base href="/"></head><body>
  <a href="DE/Anlagen/UTILMD_AHB_Strom_2_3.html?nn=861126#download=1"
     class="RichTextIntLink Publication FTpdf">UTILMD AHB Strom 2.3 (pdf / 9 MB)</a>
  <a href="DE/Anlagen/EBD_und_Codelisten_4_4.pdf?__blob=publicationFile&v=1"
     class="downloadLink Publication FTpdf">EBD und Codelisten 4.4</a>
  <a href="DE/Anlagen/Formblatt_EDIFACT.xlsx?__blob=publicationFile&v=2"
     class="downloadLink Publication FTxlsx">Formblatt EDIFACT</a>
  <a href="DE/Anlagen/UTILMD_AHB_Strom_2_3.html?nn=861126#download=1"
     class="RichTextIntLink Publication FTpdf">UTILMD AHB Strom 2.3 (duplicate)</a>
  <a href="/DE/Beschlusskammern/BK06/some_overview.html">Zur Übersicht</a>
</body></html>
"""


class TestExtractDocumentLinks:
    _PAGE_URL = "https://www.bundesnetzagentur.de/DE/Mitteilung_57/Mitteilung_Nr_57.html"

    def test_finds_all_download_links(self) -> None:
        links = extract_document_links(_BNETZA_PAGE_HTML, self._PAGE_URL)
        # 3 distinct downloads (pdf-as-html, pdf, xlsx); the plain overview link is excluded.
        assert len(links) == 3

    def test_resolves_relative_links_against_base_root(self) -> None:
        urls = [url for url, _ in extract_document_links(_BNETZA_PAGE_HTML, self._PAGE_URL)]
        # href "DE/Anlagen/..." must resolve against the site root (base href="/"), not the
        # document directory ".../Mitteilung_57/".
        assert "https://www.bundesnetzagentur.de/DE/Anlagen/UTILMD_AHB_Strom_2_3.html?nn=861126" in urls
        assert all("/Mitteilung_57/DE/" not in url for url in urls)

    def test_deduplicates_by_url_ignoring_fragment(self) -> None:
        urls = [url for url, _ in extract_document_links(_BNETZA_PAGE_HTML, self._PAGE_URL)]
        # The duplicated UTILMD link (same URL, different text) appears only once.
        assert len([u for u in urls if "UTILMD_AHB_Strom_2_3" in u]) == 1

    def test_ignores_non_download_links(self) -> None:
        urls = [url for url, _ in extract_document_links(_BNETZA_PAGE_HTML, self._PAGE_URL)]
        assert all("some_overview" not in url for url in urls)


class TestFilenameStemFromUrl:
    def test_uses_url_path_not_query(self) -> None:
        url = "https://www.bundesnetzagentur.de/DE/Anlagen/UTILMD_AHB_Strom_2_3.html?nn=861126#download=1"
        assert _filename_stem_from_url(url) == "UTILMD_AHB_Strom_2_3"

    def test_unquotes_percent_encoding(self) -> None:
        url = "https://www.bundesnetzagentur.de/DE/Anlagen/Rz%C3%9C_API-Webdienste_1_3.pdf?__blob=publicationFile"
        assert _filename_stem_from_url(url) == "RzÜ_API-Webdienste_1_3"

    def test_falls_back_when_no_name(self) -> None:
        assert _filename_stem_from_url("https://www.bundesnetzagentur.de/") == "document"


class TestDetectDocumentType:
    @staticmethod
    def _zip_with(entry: str) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(entry, "x")
        return buffer.getvalue()

    def test_detects_pdf_by_magic(self) -> None:
        assert detect_document_type(b"%PDF-1.7\n...") == "pdf"

    def test_detects_xlsx_by_zip_entry(self) -> None:
        assert detect_document_type(self._zip_with("xl/workbook.xml")) == "xlsx"

    def test_detects_docx_by_zip_entry(self) -> None:
        assert detect_document_type(self._zip_with("word/document.xml")) == "docx"

    def test_detects_html_by_body(self) -> None:
        assert detect_document_type(b"\n  <!DOCTYPE html><html></html>") == "html"

    def test_falls_back_to_content_type(self) -> None:
        # Ambiguous body, but the Content-Type header disambiguates.
        assert detect_document_type(b"random", "application/pdf; charset=UTF-8") == "pdf"

    def test_unknown_when_nothing_matches(self) -> None:
        assert detect_document_type(b"random-bytes") == "unknown"


class TestDownloadDocumentsCallbacks:
    def test_progress_callbacks_fire_per_item(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        links = [("https://x/a.pdf", "A"), ("https://x/b.pdf", "B"), ("https://x/c.pdf", "C")]

        async def fake_get_links(url: str) -> list[tuple[str, str]]:
            return links

        async def fake_download(
            client: httpx.AsyncClient, url: str, text: str, target_dir: Path, semaphore: asyncio.Semaphore
        ) -> DownloadResult:
            stem = bnetza._filename_stem_from_url(url)
            path = target_dir / f"{stem}.pdf"
            path.write_bytes(b"%PDF-1.7\n")
            return DownloadResult(url=url, text=text, stem=stem, kind="pdf", path=path, status="downloaded")

        monkeypatch.setattr(bnetza, "get_document_links", fake_get_links)
        monkeypatch.setattr(bnetza, "download_document", fake_download)
        # no change history -> no Excel written, keeps the test focused on the callbacks
        monkeypatch.setattr(bnetza, "extract_change_history_from_document", lambda path: pd.DataFrame())

        links_found: list[int] = []
        downloaded: list[str] = []
        extract_start: list[int] = []
        extracted: list[str] = []

        summary = asyncio.run(
            bnetza.download_documents(
                url="https://x/page",
                target_dir=tmp_path,
                on_links_found=links_found.append,
                on_downloaded=lambda result: downloaded.append(result.stem),
                on_extract_start=extract_start.append,
                on_extracted=extracted.append,
            )
        )

        assert links_found == [3]
        assert sorted(downloaded) == ["a", "b", "c"]  # order-independent (as_completed)
        assert extract_start == [3]
        assert sorted(extracted) == ["a.pdf", "b.pdf", "c.pdf"]
        assert summary.links_found == 3
        assert summary.downloaded == 3


class TestUniqueSheetName:
    def test_returns_name_when_unused(self) -> None:
        assert _unique_sheet_name("AHB_UTILMD", set()) == "AHB_UTILMD"

    def test_disambiguates_collision(self) -> None:
        assert _unique_sheet_name("AHB_UTILMD", {"AHB_UTILMD"}) == "AHB_UTILMD_2"

    def test_keeps_within_excel_limit(self) -> None:
        long_name = "A" * 31
        result = _unique_sheet_name(long_name, {long_name})
        assert len(result) <= 31
        assert result.endswith("_2")


class TestRowsToChangeHistoryDf:
    def test_builds_dataframe_with_header(self) -> None:
        rows = [["Änd-ID", "Ort", "Status"], ["1", "A", "done"], ["2", "B", "open"]]
        df = _rows_to_change_history_df(rows)
        assert list(df.columns) == ["Änd-ID", "Ort", "Status"]
        assert len(df) == 2

    def test_drops_empty_rows_and_pads_short_rows(self) -> None:
        rows = [["Änd-ID", "Ort", "Status"], ["1", "A"], ["", "", ""], ["2", "B", "open"]]
        df = _rows_to_change_history_df(rows)
        assert len(df) == 2  # the fully-empty row is dropped
        assert df.iloc[0].tolist() == ["1", "A", ""]  # short row padded to header width

    def test_returns_empty_for_insufficient_rows(self) -> None:
        assert _rows_to_change_history_df([["Änd-ID", "Ort"]]).empty


class TestIsChangeHistoryHeader:
    def test_matches_exact(self) -> None:
        assert _is_change_history_header("Änd-ID")

    def test_matches_line_split_header(self) -> None:
        assert _is_change_history_header("Änd-\nID")

    def test_matches_annotated_header(self) -> None:
        # e.g. APERAK AHB, whose header cell carries a trailing annotation.
        assert _is_change_history_header("Änd-ID\n…")

    def test_rejects_empty_and_other(self) -> None:
        assert not _is_change_history_header(None)
        assert not _is_change_history_header("")
        assert not _is_change_history_header("Ort")


class TestCollectSheetsData:
    def test_separates_failures_from_no_change_history(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        good = tmp_path / "AHB_UTILMD_2_3.pdf"
        empty = tmp_path / "Formblatt.xlsx"
        broken = tmp_path / "AHB_APERAK_1_1.pdf"
        for file in (good, empty, broken):
            file.write_bytes(b"x")

        def fake_extract(path: Path) -> pd.DataFrame:
            if path.name == broken.name:
                raise ValueError("corrupt document")
            if path.name == good.name:
                return pd.DataFrame({"Änd-ID": ["1"]})
            return pd.DataFrame()  # empty -> no change history

        monkeypatch.setattr(bnetza, "extract_change_history_from_document", fake_extract)

        result = _collect_sheets_data([good, empty, broken])

        assert len(result.sheets) == 1  # only the good document produced a sheet
        assert result.no_change_history == ["Formblatt.xlsx"]
        # A document that raised is a failure, NOT reported as "no change history".
        assert result.failed == ["AHB_APERAK_1_1.pdf"]
        assert broken.name not in result.no_change_history

    def test_on_extracted_called_once_per_document(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        files = [tmp_path / "AHB_UTILMD_2_3.pdf", tmp_path / "Formblatt.xlsx"]
        for file in files:
            file.write_bytes(b"x")

        monkeypatch.setattr(bnetza, "extract_change_history_from_document", lambda path: pd.DataFrame())

        seen: list[str] = []
        _collect_sheets_data(files, on_extracted=seen.append)

        # sorted by stem: Formblatt then AHB_UTILMD
        assert sorted(seen) == ["AHB_UTILMD_2_3.pdf", "Formblatt.xlsx"]
