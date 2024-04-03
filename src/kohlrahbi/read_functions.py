"""
A collection of functions to get information from AHB tables.
"""

from typing import Generator, Optional, Tuple, Union

from docx.document import Document  # type:ignore[import]
from docx.oxml.table import CT_Tbl  # type:ignore[import]
from docx.oxml.text.paragraph import CT_P  # type:ignore[import]
from docx.table import Table, _Cell  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]
from maus.edifact import EdifactFormat, get_format_of_pruefidentifikator

from kohlrahbi.ahb.ahbcondtions import AhbConditions
from kohlrahbi.ahb.ahbsubtable import AhbSubTable
from kohlrahbi.ahb.ahbtable import AhbTable
from kohlrahbi.ahb.packagetable import AhbPackageTable
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
    # seed: Seed | None,
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
    # return isinstance(item, Table) and seed is not None and ahb_table is not None
    return isinstance(item, Table) and ahb_table is not None


def is_item_package_heading(item: Paragraph | Table | None, style_name: str, edifact_format: EdifactFormat) -> bool:
    """
    Checks if the given item is the heading of the package table.
    """
    return (
        isinstance(item, Paragraph)
        and style_name == "Heading 2"
        and item.text == f"Übersicht der Pakete in der {edifact_format.name}"
    )


def get_ahb_table(document, pruefi: str) -> Optional[AhbTable]:
    """
    Reads a docx file and extracts all information for a given Prüfidentifikator.
    If the Prüfidentifikator is not found or we reach the end of the AHB document
    - indicated by the section 'Änderungshistorie' - it returns None.

    Args:
        document: AHB word document which is read by python-docx package
        pruefi (str): The Prüfidentifikator to search for

    Returns:
        AhbTable or None: The extracted AHB table or None if not found
    """

    ahb_table = None
    seed = None
    searched_pruefi_is_found = False

    for item in get_all_paragraphs_and_tables(document):
        style_name = get_style_name(item)

        if is_item_text_paragraph(item, style_name):
            continue

        if reached_end_of_document(style_name, item):
            log_end_of_document(pruefi)
            break

        seed = update_seed(item, seed)

        if should_end_search(pruefi, seed, searched_pruefi_is_found):
            log_end_of_ahb_table(pruefi)
            break

        searched_pruefi_is_found, ahb_table = process_table(item, pruefi, searched_pruefi_is_found, ahb_table, seed)

    if ahb_table:
        ahb_table.sanitize()
        return ahb_table

    log_pruefi_not_found(pruefi)
    return None


def get_style_name(item) -> str:
    """Extracts and normalizes the style name of a document item."""
    return item.style.name if item.style else "None"


def reached_end_of_document(style_name, item) -> bool:
    """Checks if the current item marks the end of the document."""
    return is_item_header_of_change_history_section(item, style_name)


def update_seed(item, seed):
    """Updates the seed if the current item is a table with Prüfidentifikatoren."""
    if is_item_table_with_pruefidentifikatoren(item):
        return Seed.from_table(docx_table=item)
    return seed


def should_end_search(pruefi, seed, searched_pruefi_is_found):
    """Determines if the search for the AHB table should end."""
    return seed and pruefi not in seed.pruefidentifikatoren and searched_pruefi_is_found


def process_table(item, pruefi, searched_pruefi_is_found, ahb_table, seed=None):
    """Processes tables to find and build the AHB table."""
    if is_item_table_with_pruefidentifikatoren(item):
        seed = Seed.from_table(docx_table=item)

        if pruefi in seed.pruefidentifikatoren and not searched_pruefi_is_found:
            log_found_pruefi(pruefi)
            ahb_sub_table = AhbSubTable.from_table_with_header(docx_table=item)
            ahb_table = AhbTable.from_ahb_sub_table(ahb_sub_table=ahb_sub_table)
            searched_pruefi_is_found = True

    # elif is_item_headless_table(item, seed, ahb_table):
    elif is_item_headless_table(item, ahb_table):
        ahb_sub_table = AhbSubTable.from_headless_table(docx_table=item, tmd=seed)
        ahb_table.append_ahb_sub_table(ahb_sub_table=ahb_sub_table)

    return searched_pruefi_is_found, ahb_table


# Logging functions
def log_end_of_document(pruefi):
    """
    Logs that the end of the document was reached before finding the table for a given Prüfi.
    """
    logger.info("Reached the end of the document before finding the table for Prüfi '%s'.", pruefi)


def log_end_of_ahb_table(pruefi):
    """
    Logs that the end of the AHB table was reached for a given Prüfi.
    """
    logger.info("Reached the end of the AHB table for Prüfi '%s'.", pruefi)


def log_found_pruefi(pruefi):
    """
    Logs that the AHB table for a given Prüfi was found.
    """
    logger.info("Found the AHB table for Prüfi '%s'.", pruefi)


def log_pruefi_not_found(pruefi):
    """
    Logs that the Prüfi was not found in the provided document.
    """
    logger.warning("Prüfi '%s' was not found in the provided document.", pruefi)


def get_package_table(document: Document) -> Optional[AhbPackageTable]:
    """
    Reads a docx file and extracts all conditions from the package table.
    If it is not found or we reached the end of the AHB document
    - indicated by the section 'Änderungshistorie' - it returns None.

    Args:
        document (Document): AHB word document which is read by python-docx package
    """

    package_table: Optional[AhbPackageTable] = None
    package_table_started: bool = False
    tables: list[Table] = []
    # Iterate through the whole word document
    logger.info("🔁 Start iterating through paragraphs and tables")
    for item in get_all_paragraphs_and_tables(parent=document):
        style_name = item.style.name  # this is a bit expensive. we should only call it once per item
        # Check if we reached the end of the current AHB document and stop if it's true.
        if isinstance(item, Paragraph) and "Änderungshistorie" in item.text and "Heading" in style_name:
            # checking the style is quite expensive for the CPU because it includes some xpath searches;
            # we should only check the style if the other (easier/cheap) checks returned True
            logger.info(
                "We reached the end of the document before any table containing the package conditions was found"
            )
            return None
        if isinstance(item, Table) and not package_table_started:
            package_table_started = item.cell(row_idx=0, col_idx=0).text.strip() == "Paket"
            if package_table_started:
                logger.info("🏁 Found Package Table")
        if isinstance(item, Table) and package_table_started:
            tables.append(item)
        if package_table_started and not isinstance(item, Table):
            logger.info("We reached the end of the package table.")
            break
    if len(tables) > 0:
        package_table = AhbPackageTable.from_docx_table(tables)
        return package_table

    logger.warning("⛔️ No package table found in the provided file.\n")
    return None


def get_all_conditions_from_doc(
    document: Document, edifact_format: EdifactFormat
) -> Tuple[Optional[AhbPackageTable], Optional[AhbConditions]]:
    """
    Go through a given document and grasp all conditions and package tables. for a given format
    """
    package_table: AhbPackageTable = None
    conditions_table: AhbConditions = None
    package_tables: list[Table] = []
    conditions_tables: list[Table] = []
    seed = None
    pruefis = []
    new_table = False
    # Iterate through the whole word document
    logger.info("🔁 Start iterating through paragraphs and tables")
    found_package_table = False
    for item in get_all_paragraphs_and_tables(document):
        style_name = get_style_name(item)
        if isinstance(item, Paragraph) and "Änderungshistorie" in item.text and "Heading" in style_name:
            logger.info(
                "Reached the end of the document, i.e. the section 'Änderungshistorie'.",
            )
        if is_item_text_paragraph(item, style_name):
            continue
        # processing of package tables
        if is_item_package_heading(item, style_name, edifact_format):
            found_package_table = True
            logger.info("🏁 Found Package Table for %s", edifact_format)
        elif isinstance(item, Table) and found_package_table:
            package_tables.append(item)
        elif found_package_table and not isinstance(item, Table):
            logger.info("We reached the end of the package table.")
            found_package_table = False

        if reached_end_of_document(style_name, item):
            log_end_of_document(edifact_format)

            break
        # processing of conditions tables
        seed = update_seed(item, seed)
        if is_ahb_table(item):
            pruefis, new_table = is_new_pruefi_table(seed, pruefis)
            if is_pruefi_of_edifact_format(pruefis, edifact_format):
                conditions_tables.append(item)
        if is_last_row_UNT_0062(item):
            seed = None
    if len(conditions_tables) > 0:
        conditions_table = AhbConditions.from_docx_table(conditions_tables)

    if len(package_tables) > 0:
        package_table = AhbPackageTable.from_docx_table(package_tables)
    return package_table, conditions_table


def is_last_row_UNT_0062(item: Table | Paragraph) -> bool:
    """
    Checks if the given table contains UNT segment in last row.
    """
    return isinstance(item, Table) and "UNT\t0062" == item.cell(row_idx=-1, col_idx=0).text.strip()


def is_ahb_table(item: Paragraph | Table) -> bool:
    """
    Checks if the given item is an AHB table.
    """
    return isinstance(item, Table) and item.cell(row_idx=0, col_idx=0).text.strip() == "EDIFACT Struktur"


def is_relevant_pruefi_table(item: Paragraph | Table, seed: Seed, edifact_format) -> bool:
    """compares new pruefis to last pruefi and thus checks whether new table"""
    return isinstance(item, Table) and seed and is_pruefi_of_edifact_format(seed.pruefidentifikatoren, edifact_format)

    is_new_table = (
        seed is not None
        and len(seed.pruefidentifikatoren) > 0
        and (last_pruefi is None or seed.pruefidentifikatoren != last_pruefi)
    )
    if is_new_table:
        return seed.pruefidentifikatoren, True
    return last_pruefi, False


def is_pruefi_of_edifact_format(last_pruefis: list[str], edifact_format: EdifactFormat) -> bool:
    """Checks if the pruefi is of the given edifact format"""
    return len(last_pruefis) > 0 and all(
        get_format_of_pruefidentifikator(pruefi) is edifact_format for pruefi in last_pruefis
    )


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
