"""Module to download and handle BNetzA PDF files."""

import asyncio
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

import httpx
import pandas as pd
import pdfplumber
from bs4 import BeautifulSoup
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

def clean_filename(text: str) -> str:
    """
    Clean up the filename by removing file size information and special characters.

    Args:
        text: The text to clean up

    Returns:
        A clean filename
    """
    # Remove the file size pattern (pdf / X MB) or (pdf / X KB)
    text = re.sub(r"\s*\(pdf\s*\/\s*\d+(?:\.\d+)?\s*[KMG]B\)", "", text)

    # Replace problematic characters
    text = text.replace("/", "_").replace(" ", "_")

    # Add .pdf extension if not present
    if not text.lower().endswith(".pdf"):
        text += ".pdf"

    return text


async def get_pdf_links(url: str) -> List[Tuple[str, str]]:
    """
    Fetch all PDF links from the given BNetzA website URL.
    Returns a list of tuples containing (filename, url).

    Args:
        url: The BNetzA page URL to scrape for PDF links.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_links = []

        # Find all links that point to PDF files
        for link in soup.find_all("a"):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            if isinstance(href, str) and ".pdf" in href:
                # Convert relative URLs to absolute URLs if necessary
                if href.startswith("/"):
                    href = f"https://www.bundesnetzagentur.de{href}"
                # Create a clean filename
                safe_filename = clean_filename(text)
                pdf_links.append((safe_filename, href))

        logger.info("Found %d PDF links to download", len(pdf_links))
        return pdf_links


async def download_pdf(client: httpx.AsyncClient, filename: str, url: str, target_path: Path) -> None:
    """
    Download a single PDF file.
    """
    if target_path.exists():
        logger.info("File %s already exists, skipping...", filename)
        return

    try:
        logger.info("Downloading %s from %s", filename, url)
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(target_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
        logger.info("Successfully downloaded %s", filename)
    except httpx.HTTPError as e:
        logger.error("Failed to download %s from %s: %s", filename, url, str(e))
    except Exception as e:
        logger.error("Unexpected error while downloading %s: %s", filename, str(e))


def rename_existing_files(directory: Path) -> None:
    """
    Rename existing files in the directory to match the new naming convention.

    Args:
        directory: The directory containing the files to rename
    """
    if not directory.exists():
        return

    for file_path in directory.glob("*.pdf"):
        old_name = file_path.name
        new_name = clean_filename(old_name)

        if old_name != new_name:
            old_path = directory / old_name
            new_path = directory / new_name
            logger.info("Renaming %s to %s", old_name, new_name)
            try:
                old_path.rename(new_path)
            except Exception as e:
                logger.error("Failed to rename %s: %s", old_name, str(e))


def cleanup_old_files(directory: Path) -> None:
    """
    Remove files with the old naming convention (containing file size information).

    Args:
        directory: The directory containing the files to clean up
    """
    if not directory.exists():
        return

    # Pattern to match files with size information in parentheses
    pattern = re.compile(r".*\(pdf___\d+(?:\.\d+)?\s*[KMG]B\)\.pdf$")

    for file_path in directory.glob("*.pdf"):
        if pattern.match(file_path.name):
            logger.info("Removing old file: %s", file_path.name)
            try:
                file_path.unlink()
            except Exception as e:
                logger.error("Failed to remove %s: %s", file_path.name, str(e))


def find_change_history_page(pdf: pdfplumber.PDF) -> int:
    """
    Find the page number where Änderungshistorie starts by checking the table of contents.

    Args:
        pdf: The opened PDF document

    Returns:
        The 0-based page index where Änderungshistorie starts, or -1 if not found
    """
    # Check first few pages for table of contents
    for page_idx, page in enumerate(pdf.pages[:4]):  # Usually TOC is in first few pages
        text = page.extract_text()
        # Look for "Änderungshistorie" followed by a page number
        matches = re.finditer(r"Änderungshistorie[.\s]+(\d+)", text)
        for match in matches:
            # Convert 1-based page number to 0-based index
            page_num = int(match.group(1)) - 1
            logger.debug("Found Änderungshistorie in TOC on page %d, pointing to page %d", page_idx + 1, page_num + 1)
            return page_num

    # Fallback: search through all pages
    for i, page in enumerate(pdf.pages):
        if "Änderungshistorie" in page.extract_text():
            logger.debug("Found Änderungshistorie text on page %d", i + 1)
            return i

    logger.debug("No Änderungshistorie section found in any page")
    return -1


def _merge_columns(cells: List[Optional[str]]) -> str:
    """Merge multiple cells into one, joining non-empty values with newlines."""
    parts = [str(c) for c in cells if c is not None and str(c).strip()]
    return "\n".join(parts) if parts else ""


def normalize_table_columns(table: List[List[Optional[str]]]) -> List[List[Optional[str]]]:
    """
    Normalize tables with 10 columns (e.g. Allgemeine Festlegungen) to the standard 6-column layout.

    The 10-column layout from pdfplumber looks like:
        [Änd-ID, Ort, _, Fehlerkorrektur/Änderung, _, _, _, _, Grund der Anpassung, Status]
        [_, _, _, Bisher, _, _, Neu, _, _, _]

    This maps to 6 logical columns:
        [Änd-ID, Ort, Bisher, Neu, Grund der Anpassung, Status]
    """
    if not table or len(table[0]) != 10:
        return table

    normalized = []
    for row in table:
        normalized.append([
            row[0],                       # Änd-ID
            row[1],                       # Ort
            _merge_columns(row[2:5]),     # Bisher (cols 2-4)
            _merge_columns(row[5:8]),     # Neu (cols 5-7)
            row[8],                       # Grund der Anpassung
            row[9],                       # Status
        ])
    return normalized


def clean_table_data(table: List[List[Optional[str]]]) -> List[List[str]]:
    """
    Clean up the table data by merging related rows before converting to DataFrame.
    Rows with empty first column should be merged with the row above.

    Args:
        table: Raw table data from PDF

    Returns:
        Cleaned table data with merged rows
    """

    if len(table) < 2:
        logger.warning("Table has insufficient rows (%d), need at least 2", len(table))
        return []

    # Get headers and sub-headers
    headers = table[0]  # First row is headers
    sub_header = table[1]  # Second row is sub-headers

    # Start with headers and sub-headers
    result = [headers]
    result.append(sub_header)

    current_row = None

    # Process each data row (skip header and sub-header)
    for row in table[2:]:
        # Convert None to empty strings in current row
        row = [str(cell) if cell is not None else "" for cell in row]
        # If first column (Änd-ID) is empty, merge with previous row
        if not row[0]:
            if current_row is not None:
                # Merge non-empty values with the current row
                for i, value in enumerate(row):
                    if value:
                        if current_row[i]:  # If current cell has content, add newline
                            current_row[i] = f"{current_row[i]}\n{value}"
                        else:  # If current cell is empty, just use new value
                            current_row[i] = value
        else:
            # If we have a previous row, add it to results
            if current_row is not None:
                result.append(current_row)
            # Start new row
            current_row = row.copy()

    # Add the last row if exists
    if current_row is not None:
        result.append(current_row)

    logger.debug("Cleaned table data: %d rows (including headers)", len(result))
    return result


def extract_change_history(pdf_path: Path) -> pd.DataFrame:
    """
    Extract the Änderungshistorie table from a PDF file.
    Specifically looks for tables that start with 'Änd-ID'.
    First finds the page number from table of contents.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        DataFrame containing the change history table
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.debug("Successfully opened PDF %s with %d pages", pdf_path.name, len(pdf.pages))
            # First find the page containing Änderungshistorie from table of contents
            change_history_page = find_change_history_page(pdf)

            if change_history_page == -1:
                logger.warning("No Änderungshistorie section found in %s", pdf_path.name)
                return pd.DataFrame()

            logger.info(
                "Found Änderungshistorie section in %s starting at page %d", pdf_path.name, change_history_page + 1
            )

            all_rows: List[List] = []

            # Scan pages from the Änderungshistorie page onwards, collecting raw rows
            for page in pdf.pages[change_history_page:]:
                tables = page.extract_tables()
                logger.debug("Page %d has %d tables", page.page_number + 1, len(tables))

                for table_idx, table in enumerate(tables):
                    if not table or not table[0]:
                        continue

                    first_cell = table[0][0]
                    is_change_history_table = first_cell == "Änd-ID" or first_cell == "Änd-\nID"

                    if is_change_history_table:
                        logger.info(
                            "Found change history table in %s on page %d (table %d)",
                            pdf_path.name,
                            page.page_number + 1,
                            table_idx + 1,
                        )
                        # Normalize 10-column tables to 6 columns
                        table = normalize_table_columns(table)
                        if not all_rows:
                            # First table: keep header and sub-header
                            all_rows.extend(table)
                        else:
                            # Subsequent tables: skip header (row 0) and sub-header (row 1)
                            all_rows.extend(table[2:])

            if all_rows:
                cleaned_table = clean_table_data(all_rows)
                if cleaned_table:
                    df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0])
                    logger.info("Extracted %d rows of change history data from %s", len(df), pdf_path.name)
                    return df

            logger.warning("No change history table found in %s", pdf_path.name)
            return pd.DataFrame()
    except Exception as e:
        logger.error("Failed to open PDF %s: %s", pdf_path.name, str(e))
        return pd.DataFrame()


def create_change_history_excel(pdf_dir: Path, output_file: Path) -> None:
    """
    Create an Excel file containing change history tables from all PDFs in the directory.

    Args:
        pdf_dir: Directory containing PDF files
        output_file: Path where the Excel file should be saved
    """
    # Check if directory exists and contains PDF files
    if not pdf_dir.exists():
        logger.error("Directory %s does not exist", pdf_dir)
        return

    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in directory %s", pdf_dir)
        return

    logger.info("Found %d PDF files to process", len(pdf_files))

    # First collect all data and sheet names
    sheets_data = []
    processed_count = 0
    for pdf_file in sorted(pdf_files, key=lambda x: x.stem):
        try:
            logger.info("Processing %s...", pdf_file.name)
            logger.info("File size: %d bytes", pdf_file.stat().st_size)

            # Check if file is readable
            if not pdf_file.is_file():
                logger.error("File %s is not a regular file", pdf_file.name)
                continue

            df = extract_change_history(pdf_file)
            if not df.empty:
                # Create sheet name with AHB/MIG prefix if present
                name = pdf_file.stem
                if "AHB" in name:
                    name = f"AHB_{name.replace('_AHB', '')}"
                elif "MIG" in name:
                    name = f"MIG_{name.replace('_MIG', '')}"
                # Excel has a 31 character limit for sheet names
                if len(name) > 31:
                    name = name[:28] + "..."
                sheets_data.append((name, df))
                processed_count += 1
                logger.info("Successfully extracted data from %s (%d rows)", pdf_file.name, len(df))
            else:
                logger.warning("No change history data found in %s", pdf_file.name)
        except Exception as e:
            logger.error("Failed to process %s: %s", pdf_file.name, str(e))
            continue

    logger.info("Successfully processed %d out of %d PDF files", processed_count, len(pdf_files))

    if not sheets_data:
        logger.error("No data extracted from any PDF files. Creating empty Excel file for testing...")
        # Create a minimal test DataFrame to ensure Excel file is created
        test_df = pd.DataFrame({"Test": ["No data found"], "Status": ["No change history data extracted from PDFs"]})
        sheets_data = [("Test", test_df)]
        logger.warning("Created test sheet with no data message")

    # Sort sheets by name
    sheets_data.sort(key=lambda x: x[0])

    # Write to Excel with sorted sheets
    logger.info("Creating Excel file at %s with %d sheets", output_file, len(sheets_data))

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            for sheet_name, df in sheets_data:
                # Write DataFrame to Excel
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Get the worksheet to adjust dimensions
                worksheet = writer.sheets[sheet_name]

                # Set fixed column widths
                column_widths = [10, 16, 33, 33, 30, 22]
                for idx, width in enumerate(column_widths):
                    worksheet.column_dimensions[chr(65 + idx)].width = width

                # Enable text wrapping for all cells
                for row in worksheet.iter_rows():
                    for cell in row:
                        cell.alignment = Alignment(wrap_text=True)

                logger.info("Successfully processed sheet %s", sheet_name)

        logger.info("Excel file created successfully at %s", output_file)
    except Exception as e:
        logger.error("Failed to create Excel file: %s", str(e))
        raise


async def download_pdfs(url: str, target_dir: Optional[Path] = None) -> None:
    """
    Download PDF files from the given BNetzA website URL and store them in the specified directory.
    If no directory is specified, creates a 'pdfs' directory next to this script.

    Args:
        url: The BNetzA page URL to scrape for PDF links.
        target_dir: Directory to store downloaded PDFs. Defaults to a 'pdfs' directory next to this script.
    """
    if target_dir is None:
        target_dir = Path(__file__).parent / "pdfs"

    target_dir.mkdir(exist_ok=True)
    logger.info("Downloading PDFs to %s", target_dir)

    # First rename any existing files
    rename_existing_files(target_dir)

    # Clean up old files
    cleanup_old_files(target_dir)

    pdf_links = await get_pdf_links(url)
    if not pdf_links:
        logger.warning("No PDF links found on the page")
        return

    logger.info("Found %d PDF files to download", len(pdf_links))
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        tasks = []
        for filename, pdf_url in pdf_links:
            target_path = target_dir / filename
            task = download_pdf(client, filename, pdf_url, target_path)
            tasks.append(task)

        logger.info("Starting download of %d PDF files...", len(tasks))
        await asyncio.gather(*tasks)
        logger.info("Download process completed")

    # After downloading, create the change history Excel file
    output_file = target_dir.parent / "change_history.xlsx"
    logger.info("Creating change history Excel file at: %s", output_file)
    logger.info("Using PDF directory: %s", target_dir)

    # Check if any PDFs were downloaded
    pdf_files_after_download = list(target_dir.glob("*.pdf"))
    logger.info("Found %d PDF files after download", len(pdf_files_after_download))

    create_change_history_excel(target_dir, output_file)

    # Check if the Excel file was actually created
    if output_file.exists():
        logger.info("Excel file successfully created at: %s", output_file)
        logger.info("File size: %d bytes", output_file.stat().st_size)
    else:
        logger.error("Excel file was not created at: %s", output_file)


def main() -> None:
    """Main entry point for the script. Expects the BNetzA URL as the first command-line argument."""
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    if len(sys.argv) < 2:
        logger.error("Usage: python -m kohlrahbi.changehistory.bnetza <BNETZA_URL>")
        sys.exit(1)

    url = sys.argv[1]
    logger.info("Starting BNetzA PDF processing for URL: %s", url)
    try:
        asyncio.run(download_pdfs(url=url))
        logger.info("BNetzA PDF processing completed successfully")
    except Exception as e:
        logger.error("BNetzA PDF processing failed: %s", str(e))
        raise


if __name__ == "__main__":
    main()
