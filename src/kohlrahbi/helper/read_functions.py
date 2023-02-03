"""
A collection of functions to get information from AHB tables.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional, Union

import pandas as pd
import pytz
from docx.document import Document  # type:ignore[import]
from docx.oxml.table import CT_Tbl  # type:ignore[import]
from docx.oxml.text.paragraph import CT_P  # type:ignore[import]
from docx.table import Table, _Cell  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]
from maus.edifact import EdifactFormatVersion, get_edifact_format_version
from more_itertools import peekable

from kohlrahbi.ahbsubtable import AhbSubTable
from kohlrahbi.ahbtable import AhbTable
from kohlrahbi.dump.flatahb import keys_that_must_no_hold_any_values
from kohlrahbi.logger import logger
from kohlrahbi.newahbtable import NewAhbTable
from kohlrahbi.seed import Seed

_ahb_file_name_pattern = re.compile(r"^(?P<name>.+Lesefassung)(?P<version>\d+\.\d+[a-z]?)(?P<suffix>.*\.docx)$")
"""
https://regex101.com/r/8A4bK8/1
"""


# pylint:disable=line-too-long
def remove_duplicates_from_ahb_list(ahb_paths: List[Path]) -> None:
    """
    Removes duplicates from the given list of AHB paths.
    In this context a duplicate is not exactly a duplicate but another AHB file that contains content but in different
    versions.
    For example, when using the Hochfrequenz edi_energy_scraper, you'll find both the regular AHB documents
    ("informatorische Lesefassung") and documents with fixes ("Konsolidierte Lesefassung mit Fehlerkorrekturen").
    We want to work only with the youngest documents and if there are two AHBs that describe the same Prüfidentifikators
    but one of them is outdated, we don't want to process it any further.
    "Youngest" means "most recent" => prefer Fehlerkorrekturen over regular documents.
    Example:
        File A: COMDISAHB-informatorischeLesefassung1.0c_99991231_20221001.docx
        File B: COMDISAHB-informatorischeLesefassung1.0cKonsolidierteLesefassungmitFehlerkorrekturenStand06.07.2022_99991231_20221001.docx
    We only want to keep File B in this case. File A shall be removed from the list.
    """
    # create a set of the names:
    normalized_file_names: List[str] = [_normalize_ahb_file_name(x) for x in ahb_paths]
    remove_items: List[Path] = []
    for ahb_path in ahb_paths:
        # first we collect the items to remove but do not remove them yet because modifying the list while iterating
        # over it is a bad idea
        ahb_path_name = _normalize_ahb_file_name(ahb_path)
        if normalized_file_names.count(ahb_path_name) > 1 and "fehlerkorrekturen" not in str(ahb_path).lower():
            remove_items.append(ahb_path)
    for remove_item in remove_items:
        ahb_paths.remove(remove_item)


def _normalize_ahb_file_name(ahb_path: Path) -> str:
    # the main idea is, that similar but not equal ahb names shall return the same (equal) string from this function
    match = _ahb_file_name_pattern.match(str(ahb_path.name))
    if match:
        return (match.groupdict()["name"] + match.groupdict()["version"]).lower()
    return str(ahb_path).lower()


def get_all_paragraphs_and_tables(parent: Union[Document, _Cell]) -> Generator[Union[Paragraph, Table], None, None]:
    """
    Yield each paragraph and table child within *parent*, in document order.
    Each returned value is an instance of either Table or Paragraph.
    *parent* would most commonly be a reference to a main Document object, but
    also works for a _Cell object, which itself can contain paragraphs and tables.
    """
    # pylint: disable=protected-access
    if isinstance(parent, Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Passed parent argument must be of type Document or _Cell")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


_validity_start_date_from_ahbname_pattern = re.compile(r"^.*(?P<germanLocalTimeStartDate>\d{8})\.docx$")
"""
https://regex101.com/r/g4wWrT/1
This pattern is strictly coupled to the edi_energy_scraper.
"""


def _get_format_version_from_ahbfile_name(ahb_docx_name: str) -> EdifactFormatVersion:
    """
    We try to extract the validity period of the AHB from its filename.
    The matching logic here is strictly coupled to the edi_energy_scraper.
    """
    match = _validity_start_date_from_ahbname_pattern.match(ahb_docx_name)
    berlin_local_time: datetime
    berlin = pytz.timezone("Europe/Berlin")
    if match:
        local_date_str = match.groupdict()["germanLocalTimeStartDate"]
        berlin_local_time = datetime.strptime(local_date_str, "%Y%m%d").astimezone(berlin)
    else:
        berlin_local_time = datetime.utcnow().astimezone(berlin)
    edifact_format_version = get_edifact_format_version(berlin_local_time)
    return edifact_format_version


def does_the_table_contain_pruefidentifikatoren(table: Table) -> bool:
    """
    Checks if the given table is a AHB table with pruefidentifikatoren.
    """

    return table.cell(row_idx=0, col_idx=0).text == "EDIFACT Struktur"


def sanitize_ahb_table_dataframe(ahb_table_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    In some cases there is the content of one cell splitted in two.
    We need to merge the content into one cell and delete the deprecated cell afterwards.
    """
    indizes_of_to_delete_rows: list[int] = []

    def line_contains_only_segment_gruppe(raw_line: pd.Series) -> bool:
        """
        returns true if the given raw line only contains some meaningful data in the "Segment Gruppe" key
        """
        for row_key in keys_that_must_no_hold_any_values:
            if row_key in raw_line and raw_line[row_key] is not None and len(raw_line[row_key].strip()) > 0:
                return False
        return True

    iterable_ahb_table = peekable(ahb_table_dataframe.iterrows())

    for _, row in iterable_ahb_table:
        index_of_next_row, next_row = iterable_ahb_table.peek(
            (
                0,
                pd.Series(
                    {
                        "Segment Gruppe": "",
                        "Segment": "",
                        "Codes und Qualifier": "",
                        "Beschreibung": "",
                        "Bedingung": "",
                    }
                ),
            )
        )

        if (
            "Segment Gruppe" in row
            and row["Segment Gruppe"]
            and line_contains_only_segment_gruppe(row)
            and not next_row["Segment Gruppe"].startswith("SG")
            and not next_row["Segment"]
        ):
            merged_segment_gruppe_content = " ".join([row["Segment Gruppe"], next_row["Segment Gruppe"]])
            row["Segment Gruppe"] = merged_segment_gruppe_content.strip()

            if isinstance(index_of_next_row, int):
                if index_of_next_row == 0:
                    # this case is only for the first and last row. These lines should not get deleted.
                    continue
                indizes_of_to_delete_rows.append(index_of_next_row)
            else:
                raise TypeError(f"The 'index_of_next_row' must by of type `int` but it is '{type(index_of_next_row)}'")

    def drop_unnecessary_lines(df: pd.DataFrame, lines_to_drop: list[int]) -> pd.DataFrame:
        """ """

        cleaned_df = df.drop(lines_to_drop)
        cleaned_df = cleaned_df.reset_index(drop=True)

        return cleaned_df

    return drop_unnecessary_lines(df=ahb_table_dataframe, lines_to_drop=indizes_of_to_delete_rows)


# pylint: disable=inconsistent-return-statements
def get_kohlrahbi(
    document: Document, root_output_directory_path: Path, ahb_file_name: Path, pruefi: str
) -> Optional[pd.DataFrame]:
    """Reads a docx file and extracts all information for each Prüfidentifikator.

    Args:
        document (Document): AHB which is read by python-docx package
        output_directory_path (Path): Location of the output files
        ahb_file_name (str): Name of the AHB document

    Returns:
        int: Error code, 0 means success
    """

    seed: Optional[Seed] = None
    edifact_format_version: EdifactFormatVersion = _get_format_version_from_ahbfile_name(str(ahb_file_name))
    logger.info("Extracted format version: %s", edifact_format_version)
    output_directory_path: Path = root_output_directory_path / str(edifact_format_version)
    logger.info("The output directory is: %s", output_directory_path)

    ahb_table_dataframe: Optional[pd.DataFrame] = None
    new_ahb_table: Optional[NewAhbTable] = None
    is_ahb_table_initialized: bool = False
    searched_pruefi_is_found: bool = False

    # Iterate through the whole word document
    logger.info("Start iterating through paragraphs and tables")
    for item in get_all_paragraphs_and_tables(parent=document):
        # Check if we reached the end of the current AHB document and stop if it's true.
        if isinstance(item, Paragraph) and "Heading" in item.style.name and "Änderungshistorie" in item.text:
            return None

        # Check if there is just a text paragraph,
        if isinstance(item, Paragraph) and not "Heading" in item.style.name:
            continue

        if isinstance(item, Table) and does_the_table_contain_pruefidentifikatoren(table=item):
            # check which pruefis
            seed = Seed.from_table(docx_table=item)
            logger.info("Found a table with the following pruefis: %s", seed.pruefidentifikatoren)

        we_reached_the_end_of_the_ahb_table_of_the_searched_pruefi: bool = (
            seed is not None and pruefi not in seed.pruefidentifikatoren and searched_pruefi_is_found
        )

        # @konstantin: Wie war nochmal die Reihenfolge in Python in der die Bedingungen geprüft werden?
        if we_reached_the_end_of_the_ahb_table_of_the_searched_pruefi:
            seed = None
            logger.info("🏁 We reached the end of the AHB table of the Prüfidentifikator '%s'", pruefi)
            break

        if isinstance(item, Table) and does_the_table_contain_pruefidentifikatoren(table=item):
            # check which pruefis
            seed = Seed.from_table(docx_table=item)
            logger.info("Found a table with the following pruefis: %s", seed.pruefidentifikatoren)

            if pruefi in seed.pruefidentifikatoren and not is_ahb_table_initialized:
                logger.info("👀 Found the AHB table with the Prüfidentifkator you are looking for %s", pruefi)
                searched_pruefi_is_found = True
                logger.info("✨ Initializing new ahb table dataframe")

                ahb_sub_table = AhbSubTable.from_table_with_header(docx_table=item)

                new_ahb_table = NewAhbTable.from_ahb_sub_table(ahb_sub_table=ahb_sub_table)

                # ahb_table_dataframe = pd.DataFrame(
                #     columns=seed.column_headers,
                #     dtype="str",
                # )
                is_ahb_table_initialized = True

                # ahb_table: AhbTable = AhbTable(seed=seed, docx_table=item)

                # ahb_table_dataframe = ahb_table.parse(ahb_table_dataframe=ahb_table_dataframe)
                continue
        if isinstance(item, Table) and seed is not None and new_ahb_table is not None:
            ahb_sub_table = AhbSubTable.from_headless_table(docx_table=item, tmd=ahb_sub_table.table_meta_data)
            new_ahb_table.append_ahb_sub_table(ahb_sub_table=ahb_sub_table)

            # ahb_table = AhbTable(seed=seed, docx_table=item)
            # ahb_table_dataframe = ahb_table.parse(ahb_table_dataframe=ahb_table_dataframe)

    if new_ahb_table is None:
        logger.warning("⛔️ Your searched pruefi '%s' was not found in the provided files.\n", pruefi)
        return None

    # sanitize dataframe here
    # final_ahb_dataframe = sanitize_ahb_table_dataframe(ahb_table_dataframe=ahb_table_dataframe)
    new_ahb_table.sanitize_ahb_table()

    return new_ahb_table.table
