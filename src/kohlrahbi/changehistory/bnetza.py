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

logger = logging.getLogger(__name__)

BNETZA_URL = "https://www.bundesnetzagentur.de/DE/Beschlusskammern/BK06/BK6_83_Zug_Mess/835_mitteilungen_datenformate/Mitteilung_48/Mitteilung_Nr_48.html?nn=875498"

# List of EDIFACT documents to download
EDIFACT_DOCUMENTS = [
    "Anwendungsübersicht der Prüfindikatoren 3.2",
    "APERAK AHB 1.0",
    "COMDIS AHB 1.0g",
    "COMDIS MIG 1.0f",
    "CONTRL AHB 1.0",
    "IFTSTA AHB 2.0h",
    "IFTSTA MIG 2.0g",
    "INVOIC AHB 1.0",
    "INVOIC MIG 2.8e",
    "ORDERS AHB 1.1",
    "ORDERS MIG 1.4b",
    "ORDRSP AHB 1.1",
    "ORDRSP MIG 1.4a",
    "PRICAT AHB 2.0f",
    "PRICAT MIG 2.0e",
    "QUOTES AHB 1.1",
    "QUOTES MIG 1.3b",
    "REMADV AHB 1.0",
    "REMADV MIG 2.9d",
    "REQOTE AHB 1.1",
    "REQOTE MIG 1.3c",
    "Codeliste der Artikelnummern und Artikel-ID 5.6",
    "Entscheidungsbaum-Diagramme und Codelisten 4.1",
]


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


async def get_pdf_links() -> List[Tuple[str, str]]:
    """
    Fetch PDF links from the BNetzA website.
    Returns a list of tuples containing (filename, url).
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(BNETZA_URL)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_links = []

        # Find all links that contain PDF files
        for link in soup.find_all("a"):
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # Check if the link text matches any of our target documents
            for doc in EDIFACT_DOCUMENTS:
                if doc in text and isinstance(href, str):
                    # Convert relative URLs to absolute URLs if necessary
                    if href.startswith("/"):
                        href = f"https://www.bundesnetzagentur.de{href}"
                    # Create a clean filename
                    safe_filename = clean_filename(text)
                    pdf_links.append((safe_filename, href))
                    break

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
    for page in pdf.pages[:4]:  # Usually TOC is in first few pages
        text = page.extract_text()
        # Look for "Änderungshistorie" followed by a page number
        matches = re.finditer(r"Änderungshistorie[.\s]+(\d+)", text)
        for match in matches:
            # Convert 1-based page number to 0-based index
            return int(match.group(1)) - 1

    # Fallback: search through all pages
    for i, page in enumerate(pdf.pages):
        if "Änderungshistorie" in page.extract_text():
            return i

    return -1


def clean_table_data(table: List[List[Optional[str]]]) -> List[List[str]]:
    """
    Clean up the table data by merging related rows before converting to DataFrame.
    Rows with empty first column should be merged with the row above.

    Args:
        table: Raw table data from PDF

    Returns:
        Cleaned table data with merged rows
    """

    assert len(table) > 2, "Need at least headers rows"

    # Get headers and sub-headers
    headers = table[0]  # First row is headers
    sub_header = table[1]  # Second row is sub-headers

    # Start with headers and sub-headers
    result = [headers]
    result.append(sub_header)

    current_row = None

    # Process each data row (skip header)
    for row in table[1:]:
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
    with pdfplumber.open(pdf_path) as pdf:
        # First find the page containing Änderungshistorie from table of contents
        change_history_page = find_change_history_page(pdf)

        if change_history_page == -1:
            logger.warning("No Änderungshistorie section found in %s", pdf_path.name)
            return pd.DataFrame()

        # Now only scan pages from the Änderungshistorie page onwards
        for page in pdf.pages[change_history_page:]:
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 0 and table[0] and table[0][0] == "Änd-ID":
                    # Clean up the table data before converting to DataFrame
                    cleaned_table = clean_table_data(table)
                    # Convert to DataFrame
                    df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0])
                    return df

    logger.warning("No change history table found in %s", pdf_path.name)
    return pd.DataFrame()


def create_change_history_excel(pdf_dir: Path, output_file: Path) -> None:
    """
    Create an Excel file containing change history tables from all PDFs in the directory.

    Args:
        pdf_dir: Directory containing PDF files
        output_file: Path where the Excel file should be saved
    """
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Get all PDF files and sort them alphabetically
        pdf_files = sorted(pdf_dir.glob("*.pdf"), key=lambda x: x.stem)

        for pdf_file in pdf_files:
            try:
                df = extract_change_history(pdf_file)
                if not df.empty:
                    # Use the filename without extension as sheet name
                    sheet_name = pdf_file.stem
                    # Excel has a 31 character limit for sheet names
                    if len(sheet_name) > 31:
                        sheet_name = sheet_name[:28] + "..."

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

                    logger.info("Successfully processed %s", pdf_file.name)
                else:
                    logger.warning("No data extracted from %s", pdf_file.name)
            except Exception as e:
                logger.error("Failed to process %s: %s", pdf_file.name, str(e))
                continue


async def download_pdfs(target_dir: Optional[Path] = None) -> None:
    """
    Download PDF files from the BNetzA website and store them in the specified directory.
    If no directory is specified, creates a 'pdfs' directory next to this script.
    """
    if target_dir is None:
        target_dir = Path(__file__).parent / "pdfs"

    target_dir.mkdir(exist_ok=True)
    logger.info("Downloading PDFs to %s", target_dir)

    # First rename any existing files
    rename_existing_files(target_dir)

    # Clean up old files
    cleanup_old_files(target_dir)

    pdf_links = await get_pdf_links()
    if not pdf_links:
        logger.warning("No PDF links found on the page")
        return

    logger.info("Found %d PDF files to download", len(pdf_links))
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        tasks = []
        for filename, url in pdf_links:
            target_path = target_dir / filename
            task = download_pdf(client, filename, url, target_path)
            tasks.append(task)

        await asyncio.gather(*tasks)

    # After downloading, create the change history Excel file
    output_file = target_dir.parent / "change_history.xlsx"
    create_change_history_excel(target_dir, output_file)


def main() -> None:
    """Main entry point for the script."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    asyncio.run(download_pdfs())


if __name__ == "__main__":
    main()
