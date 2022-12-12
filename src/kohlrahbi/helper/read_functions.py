"""
A collection of functions to get information from AHB tables.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Tuple, Union

import pytz
from docx.document import Document  # type:ignore[import]
from docx.oxml.table import CT_Tbl  # type:ignore[import]
from docx.oxml.text.paragraph import CT_P  # type:ignore[import]
from docx.table import Table, _Cell  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]
from maus.edifact import EdifactFormatVersion, get_edifact_format_version

from kohlrahbi import logger
from kohlrahbi.helper.export_functions import (
    export_all_pruefidentifikatoren_in_one_file,
    export_single_pruefidentifikator,
)
from kohlrahbi.helper.row_type_checker import RowType, get_row_type
from kohlrahbi.helper.seed import Seed
from kohlrahbi.helper.write_functions import parse_ahb_table_row

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


# pylint: disable=too-many-arguments
def read_table(
    seed: Seed,
    table: Table,
) -> List[RowType]:
    """
    Iterates through all rows in a given table and writes all extracted infos in a DataFrame.

    Args:
        table (Table): Current table in the docx
        dataframe (pd.DataFrame): Contains all infos of the Prüfidentifikators
        current_df_row_index (int): Current row of the dataframe
        last_two_row_types (List[RowType]): Contains the two last RowType. Is needed for the case of empty rows.
        edifact_struktur_cell_left_indent_position (int): Position of the left indent in the
            indicator edifact struktur cell
        middle_cell_left_indent_position (int): Position of the left indent in the indicator middle cell
        tabstop_positions (List[int]): All tabstop positions of the indicator middle cell

    Returns:
        Tuple[List[RowType], int]: Last two RowTypes and the new row index for the DataFrame
    """
    # pylint: disable=protected-access
    if table._column_count == 4:
        index_for_middle_column = 2
    else:
        index_for_middle_column = 1

    for row in range(len(table.rows)):

        # initial empty list for the next row in the dataframe
        seed.soul.loc[0] = (len(seed.soul.columns)) * [""]

        row_cell_texts_as_list = [cell.text for cell in table.row_cells(row)]

        # pylint: disable=protected-access
        if table._column_count == 4:
            # remove redundant information for tables with 4 columns
            if (
                row_cell_texts_as_list[0] == row_cell_texts_as_list[1]
                and row_cell_texts_as_list[2] == row_cell_texts_as_list[3]
            ):
                # pylint: disable=line-too-long
                # HEADER looks like
                # 0:'EDIFACT Struktur'
                # 1:'EDIFACT Struktur'
                # 2:'Beschreibung\tKündigung\tBestätigung\tAblehnung\tBedingung\n\tMSB \tKündigung\tKündigung\n\tMSB \tMSB \nKommunikation von\tMSBN an\tMSBA an\tMSBA an\n\tMSBA\tMSBN\tMSBN\nPrüfidentifikator\t11039\t11040\t11041'
                # 3:'Beschreibung\tKündigung\tBestätigung\tAblehnung\tBedingung\n\tMSB \tKündigung\tKündigung\n\tMSB \tMSB \nKommunikation von\tMSBN an\tMSBA an\tMSBA an\n\tMSBA\tMSBN\tMSBN\nPrüfidentifikator\t11039\t11040\t11041'
                # len():4
                del row_cell_texts_as_list[1]
                row_cell_texts_as_list[2] = ""
            elif row_cell_texts_as_list[1] == row_cell_texts_as_list[2]:
                # Dataelement row with header in the table
                # 0:'SG2\tNAD\t3035'
                # 1:'SG2\tNAD\t3035'
                # 2:'MR\tNachrichtenempfänger\tX\tX\tX'
                # 3:''
                # len():4
                del row_cell_texts_as_list[1]
            elif row_cell_texts_as_list[0] == row_cell_texts_as_list[1]:
                del row_cell_texts_as_list[1]

        current_edifact_struktur_cell = table.row_cells(row)[0]

        # check for row type
        current_row_type = get_row_type(
            edifact_struktur_cell=current_edifact_struktur_cell,
            left_indent_position=seed.edifact_struktur_left_indent_position,
        )

        # write actual row into dataframe

        # this case covers the "normal" docx table row
        if not (current_row_type is RowType.EMPTY and seed.last_two_row_types[0] is RowType.HEADER):
            parse_ahb_table_row(
                row_type=current_row_type,
                ahb_table=table,
                ahb_table_row=row,
                index_for_middle_column=index_for_middle_column,
                seed=seed,
            )
        # this case covers the page break situation
        # the current RowType is EMPTY and the row before is of RowTyp HEADER
        # important is here to decrease the current_df_row_index by one to avoid an empty row in the output file
        # which only contains the Bedingung.
        else:
            is_appending = True

            parse_ahb_table_row(
                row_type=seed.last_two_row_types[1],
                ahb_table=table,
                ahb_table_row=row,
                index_for_middle_column=index_for_middle_column,
                seed=seed,
                is_appending=is_appending,
            )

        # remember last row type for empty cells
        seed.last_two_row_types[1] = seed.last_two_row_types[0]
        seed.last_two_row_types[0] = current_row_type

    return seed.last_two_row_types


_validity_start_date_from_ahbname_pattern = re.compile(r"^.*(?P<germanLocalTimeStartDate>\d{8})\.docx$")
"""
https://regex101.com/r/g4wWrT/1
This pattern is strictly coupled to the edi_energy_scraper.
"""


def _export_format_version_from_ahbfile_name(ahb_docx_name: str) -> EdifactFormatVersion:
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


# pylint: disable=inconsistent-return-statements
def get_kohlrahbi(document: Document, output_directory_path: Path, ahb_file_name: Path) -> int:
    """Reads a docx file and extracts all information for each Prüfidentifikator.

    Args:
        document (Document): AHB which is read by python-docx package
        output_directory_path (Path): Location of the output files
        ahb_file_name (str): Name of the AHB document

    Returns:
        int: Error code, 0 means success
    """

    is_initial_run = True
    seed: Seed
    edifact_format_version = _export_format_version_from_ahbfile_name(str(ahb_file_name))
    output_directory_path = output_directory_path / str(edifact_format_version)
    # Iterate through the whole word document
    for item in get_all_paragraphs_and_tables(parent=document):

        # Check if there is just a text paragraph,
        if isinstance(item, Paragraph) and not "Heading" in item.style.name:
            continue

        # Check if the paragraph is a chapter or section title
        if isinstance(item, Paragraph) and "Heading" in item.style.name:
            current_chapter_title = item.text

            # Stop iterating at the section "Änderungshistorie"
            if current_chapter_title == "Änderungshistorie":
                # export last pruefidentifikatoren in AHB
                # elixir should have been initialized here, because the document is at the end of the document
                for pruefi in seed.pruefidentifikatoren:  # pylint:disable=used-before-assignment

                    export_single_pruefidentifikator(
                        pruefi=pruefi,
                        df=seed.soul,
                        output_directory_path=output_directory_path,
                    )

                    export_all_pruefidentifikatoren_in_one_file(
                        pruefi=pruefi,
                        df=seed.soul,
                        output_directory_path=output_directory_path,
                        file_name=ahb_file_name,
                    )

                # I don't know how to exit the program without a return
                return 0

        # Check if a table comes with new Prüfidentifikatoren
        elif isinstance(item, Table) and item.cell(row_idx=0, col_idx=0).text == "EDIFACT Struktur":
            # before we go to the next pruefidentifikatoren we save the current ones
            # but at the first loop we check if list of pruefidentifikatoren is empty
            if is_initial_run is False:
                for pruefi in seed.pruefidentifikatoren:

                    export_single_pruefidentifikator(
                        pruefi=pruefi,
                        df=seed.soul,
                        output_directory_path=output_directory_path,
                    )

                    export_all_pruefidentifikatoren_in_one_file(
                        pruefi=pruefi,
                        df=seed.soul,
                        output_directory_path=output_directory_path,
                        file_name=ahb_file_name,
                    )

            seed = Seed.from_table(docx_table=item)
            comma_separated_pruefis = ", ".join(seed.pruefidentifikatoren)
            logger.info("🔍 Extracting Pruefidentifikatoren: %s", comma_separated_pruefis)
            read_table(
                seed=seed,
                table=item,
            )

            is_initial_run = False

        elif isinstance(item, Table) and "seed" in locals():
            read_table(
                seed=seed,
                table=item,
            )
    return 0  # you need to return something when the type hint states that you return something
