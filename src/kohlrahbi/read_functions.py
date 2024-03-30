"""
A collection of functions to get information from AHB tables.
"""

from typing import Generator, Optional, Union

from docx.document import Document  # type:ignore[import]
from docx.oxml.table import CT_Tbl  # type:ignore[import]
from docx.oxml.text.paragraph import CT_P  # type:ignore[import]
from docx.table import Table, _Cell  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]

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


def does_the_table_contain_pruefidentifikatoren(table: Table) -> bool:
    """
    Checks if the given table is a AHB table with pruefidentifikatoren.
    """

    return table.cell(row_idx=0, col_idx=0).text.strip() == "EDIFACT Struktur"


def is_item_header_of_change_history_section(item: Paragraph | Table | None, style_name: str) -> bool:
    """
    Checks if the given item is a header of the change history section.
    """
    # checking the style is quite expensive for the CPU because it includes some xpath searches;
    # we should only check the style if the other (easier/cheap) checks returned True so it at least
    return isinstance(item, Paragraph) and "Änderungshistorie" in item.text and "Heading" in style_name


def is_item_text_paragraph(item: Paragraph | Table | None, style_name: str) -> bool:
    """
    Checks if the given item is a text paragraph.
    """
    return isinstance(item, Paragraph) and "Heading" not in style_name


def is_item_table_with_pruefidentifikatoren(item: Paragraph | Table | None) -> bool:
    """
    Check if the item is a Table and contains Pruefidentifikatoren.

    Args:
    item (Paragraph | Table | None): The item to check.

    Returns:
    bool: True if the item is a Table and contains Pruefidentifikatoren, False otherwise.
    """
    return isinstance(item, Table) and does_the_table_contain_pruefidentifikatoren(table=item)


def is_item_headless_table(
    item: Paragraph | Table | None,
    seed: Seed | None,
    ahb_table: AhbTable | None,
) -> bool:
    """
    Checks if the given item is a headless table.

    Args:
        item (Paragraph | Table | None): The item to be checked.
        seed (Seed): The seed object.
        ahb_table (AhbTable): The AhbTable object.

    Returns:
        bool: True if the item is a headless table, False otherwise.
    """
    return isinstance(item, Table) and seed is not None and ahb_table is not None


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
        if isinstance(style_name, type(None)):
            style_name = "None"
        # Check if we reached the end of the current AHB document and stop if it's true.
        if is_item_header_of_change_history_section(item, style_name):
            logger.info(
                "We reached the end of the document before any table containing the searched Prüfi %s was found", pruefi
            )
            del seed
            return None

        # Check if there is just a text paragraph,
        if is_item_text_paragraph(item, style_name):
            continue

        if is_item_table_with_pruefidentifikatoren(item):
            # check which pruefis
            seed = Seed.from_table(docx_table=item)
            logger.debug("Found a table with the following pruefis (A): %s", seed.pruefidentifikatoren)

        is_end_of_searched_pruefi_table_reached: bool = (
            seed is not None and pruefi not in seed.pruefidentifikatoren and searched_pruefi_is_found
        )

        if is_end_of_searched_pruefi_table_reached:
            del seed
            seed = None
            logger.info("🏁 We reached the end of the AHB table of the Prüfidentifikator '%s'", pruefi)
            break

        if is_item_table_with_pruefidentifikatoren(item):
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
        if is_item_headless_table(item, seed, ahb_table):
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
