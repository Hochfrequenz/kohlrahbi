"""
A collection of functions to get information from AHB tables.
"""
import re
from datetime import datetime
from typing import Generator, Optional, Union

import pytz
from docx.document import Document  # type:ignore[import]
from docx.oxml.table import CT_Tbl  # type:ignore[import]
from docx.oxml.text.paragraph import CT_P  # type:ignore[import]
from docx.table import Table, _Cell  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]
from maus.edifact import EdifactFormatVersion, get_edifact_format_version

from kohlrahbi.ahb.ahbsubtable import AhbSubTable
from kohlrahbi.ahb.ahbtable import AhbTable
from kohlrahbi.changehistory.changehistorytable import ChangeHistoryTable
from kohlrahbi.logger import logger
from kohlrahbi.seed import Seed


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
https://github.com/Hochfrequenz/edi_energy_scraper/blob/9cc6552d0bf655f98a09f0d3500a5736c68c9c01/src/edi_energy_scraper/__init__.py#L261
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

    return table.cell(row_idx=0, col_idx=0).text.strip() == "EDIFACT Struktur"


def get_ahb_table(document: Document, pruefi: str) -> Optional[AhbTable]:
    """
    Reads a docx file and extracts all information for each Prüfidentifikator.
    If the Prüfidentifikator is not found or we reached the end of the AHB document
    - indicated by the section 'Änderungshistorie' - it returns None.

    Args:
        document (Document): AHB word document which is read by python-docx package
    """

    seed: Optional[Seed] = None

    ahb_table: Optional[AhbTable] = None
    is_ahb_table_initialized: bool = False
    searched_pruefi_is_found: bool = False

    # Iterate through the whole word document
    logger.info("🔁 Start iterating through paragraphs and tables")
    for item in get_all_paragraphs_and_tables(parent=document):
        style_name = item.style.name  # this is a bit expensive. we should only call it once per item
        # Check if we reached the end of the current AHB document and stop if it's true.
        if isinstance(item, Paragraph) and "Änderungshistorie" in item.text and "Heading" in style_name:
            # checking the style is quite expensive for the CPU because it includes some xpath searches;
            # we should only check the style if the other (easier/cheap) checks returned True
            logger.info(
                "We reached the end of the document before any table containing the searched Prüfi %s was found", pruefi
            )
            del seed
            return None

        # Check if there is just a text paragraph,
        if isinstance(item, Paragraph) and not "Heading" in style_name:
            continue

        if isinstance(item, Table) and does_the_table_contain_pruefidentifikatoren(table=item):
            # check which pruefis
            seed = Seed.from_table(docx_table=item)
            logger.debug("Found a table with the following pruefis (A): %s", seed.pruefidentifikatoren)

        we_reached_the_end_of_the_ahb_table_of_the_searched_pruefi: bool = (
            seed is not None and pruefi not in seed.pruefidentifikatoren and searched_pruefi_is_found
        )

        if we_reached_the_end_of_the_ahb_table_of_the_searched_pruefi:
            del seed
            seed = None
            logger.info("🏁 We reached the end of the AHB table of the Prüfidentifikator '%s'", pruefi)
            break

        if isinstance(item, Table) and does_the_table_contain_pruefidentifikatoren(table=item):
            # check which pruefis
            seed = Seed.from_table(docx_table=item)
            logger.debug("Found a table with the following pruefis (B): %s", seed.pruefidentifikatoren)

            searched_pruefi_is_found = pruefi in seed.pruefidentifikatoren and not is_ahb_table_initialized

            if searched_pruefi_is_found:
                logger.info("👀 Found the AHB table with the Prüfidentifkator you are looking for %s", pruefi)
                logger.info("✨ Initializing new ahb table")

                ahb_sub_table = AhbSubTable.from_table_with_header(docx_table=item)

                ahb_table = AhbTable.from_ahb_sub_table(ahb_sub_table=ahb_sub_table)

                is_ahb_table_initialized = True
                continue
        if isinstance(item, Table) and seed is not None and ahb_table is not None:
            ahb_sub_table = AhbSubTable.from_headless_table(docx_table=item, tmd=ahb_sub_table.table_meta_data)
            ahb_table.append_ahb_sub_table(ahb_sub_table=ahb_sub_table)

    if ahb_table is None:
        logger.warning("⛔️ Your searched pruefi '%s' was not found in the provided files.\n", pruefi)
        return None

    ahb_table.sanitize()
    del seed
    return ahb_table


def is_change_history_table(table: Table) -> bool:
    """
    Checks if the given table is change history table.
    """
    # in the document 'Entscheidungsbaum-DiagrammeundCodelisten-informatorischeLesefassung3.5_99991231_20240401.docx'
    # I got the error "IndexError: list index out of range", I am not sure which table caused the error
    try:
        return table.cell(row_idx=0, col_idx=0).text.strip() == "Änd-ID"
    except IndexError:
        return False


def get_change_history_table(document: Document) -> Optional[ChangeHistoryTable]:
    """
    Reads a docx file and extracts the change history.
    Returns None if no such table was found.
    """

    # Iterate through the whole word document
    logger.info("🔁 Start iterating through paragraphs and tables")
    for item in get_all_paragraphs_and_tables(parent=document):
        if isinstance(item, Table) and is_change_history_table(table=item):
            change_history_table = ChangeHistoryTable.from_docx_change_history_table(docx_table=item)
            return change_history_table

    return None
