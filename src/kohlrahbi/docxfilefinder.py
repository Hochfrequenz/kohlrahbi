"""
This module contains the DocxFileFinder class.
"""

import re
from itertools import groupby
from pathlib import Path

from efoli import EdifactFormat, get_format_of_pruefidentifikator
from more_itertools import last
from pydantic import BaseModel

from kohlrahbi.logger import logger


class EdiEnergyDocument(BaseModel):
    """
    This class represents an EDI Energy document.
    """

    filename: Path
    document_version: str
    valid_from_date: int
    valid_until_date: int

    @classmethod
    def from_path(cls, path: Path) -> "EdiEnergyDocument":
        """
        Create an EdiEnergyDocument object from a file path.
        """

        document_version, valid_from_date, valid_until_date = extract_document_version_and_valid_dates(path.name)

        return cls(
            filename=path,
            document_version=document_version,
            valid_from_date=int(valid_from_date),
            valid_until_date=int(valid_until_date),
        )

    def __lt__(self, other: "EdiEnergyDocument") -> bool:
        """
        Compare two EdiEnergyDocument instances based on their document_version, valid_until_date, and valid_from_date.

        I did not know how the tuple comparison works in Python, so I looked it up:

        Python compares tuples lexicographically, meaning it compares the elements one by one from left to right.
        The comparison starts with the first elements of both tuples:
          If self.document_version is less than other.document_version, the entire expression evaluates to True.
          If self.document_version is greater than other.document_version, the entire expression evaluates to False.
          If self.document_version is equal to other.document_version, Python moves to the next elements in the tuples.
        This process continues with self.valid_until_date vs. other.valid_until_date and then self.valid_from_date vs.
        other.valid_from_date.

        Args:
            other (EdiEnergyDocument): The other document to compare against.

        Returns:
            bool: True if this document is considered less than the other document, False otherwise.
        """
        return (self.document_version, self.valid_until_date, self.valid_from_date) < (
            other.document_version,
            other.valid_until_date,
            other.valid_from_date,
        )


def extract_document_version_and_valid_dates(filename: str) -> tuple[str, str, str]:
    """Extract the document version and valid dates from the filename.

    Parameters:
    - filename (str): The filename of the document.

    Returns:
    - tuple[str, str, str]: A tuple containing the document version, valid from date, and valid until date.
    """

    # Pattern to extract version number after '-informatorischeLesefassung'
    docment_version_pattern = r"-informatorischeLesefassung([A-Za-z0-9.]+)"
    # Pattern to extract the two dates at the end
    date_pattern = r"_(\d{8})_(\d{8})\.docx$"

    # Extract version
    version_match = re.search(docment_version_pattern, filename)
    document_version = version_match.group(1) if version_match else ""

    # Extract dates
    date_match = re.search(date_pattern, filename)
    if date_match:
        valid_from_date = date_match.group(1)
        valid_until_date = date_match.group(2)
    else:
        valid_from_date = ""
        valid_until_date = ""

    return document_version, valid_from_date, valid_until_date


def get_most_recent_file(group_items: list[Path]) -> Path | None:
    """
    Find the most recent file in a group of files based on specific criteria.

    Parameters:
    - group_items (List[Path]): A list of Path objects representing the file paths.

    Returns:
    - Path: A Path object representing the most recent file.
    """

    try:
        # Define the keywords to filter relevant files
        keywords = [
            "konsolidiertelesefassungmitfehlerkorrekturen",
            "außerordentlicheveröffentlichung",
            "informatorischelesefassung",
        ]

        # Find the most recent file based on keywords and date suffixes
        list_of_paths = [path for path in group_items if any(keyword in path.name.lower() for keyword in keywords)]

        list_of_edi_energy_documents = [EdiEnergyDocument.from_path(path) for path in list_of_paths]

        most_recent_file = max(list_of_edi_energy_documents)

        return most_recent_file.filename

    except ValueError as e:
        logger.error("Error processing group items: %s", e)
        return None


class DocxFileFinder(BaseModel):
    """
    This class is responsible for finding the docx files in the input directory.
    It can find MIG and AHB docx files.
    """

    paths_to_docx_files: list[Path]

    @classmethod
    def from_input_path(cls, input_path: Path) -> "DocxFileFinder":
        """
        Create an DocxFileFinder object from the input path.
        """

        ahb_file_paths: list[Path] = [path for path in input_path.iterdir() if path.is_file() if path.suffix == ".docx"]
        if not any(ahb_file_paths):  # this is suspicious at least
            logger.warning("The directory '%s' does not contain any docx files.", input_path.absolute())
        return cls(paths_to_docx_files=ahb_file_paths)

    @staticmethod
    def get_first_part_of_ahb_docx_file_name(path_to_ahb_document: Path) -> str:
        """
        Return the first part of the AHB docx file name.
        The first part contains the information about the EDIFACT formats.
        """

        return path_to_ahb_document.name.split("-")[0]

    def filter_for_latest_ahb_docx_files(self) -> None:
        """
        Filter the list of AHB docx paths for the latest AHB docx files.
        The latest files contain `LesefassungmitFehlerkorrekturen` in their file names.
        This method is _not_ pure. It changes the state of the object.
        """
        self.paths_to_docx_files = self.filter_ahb_docx_files(self.paths_to_docx_files)
        grouped_files = self.group_files_by_name_prefix(self.paths_to_docx_files)
        self.paths_to_docx_files = self.filter_latest_version(grouped_files)

    @staticmethod
    def filter_ahb_docx_files(paths_to_docx_files: list[Path]) -> list[Path]:
        """
        This function filters the docx files which contain the string "AHB" in their file name.
        """
        return [path for path in paths_to_docx_files if "AHB" in path.name]

    @staticmethod
    def filter_for_docx_files_with_change_history(paths_to_docx_files: list[Path]) -> list[Path]:
        """
        This function filters the docx files which contain a change history.
        At this time it seems that all docx files have a change history.
        But this may change in the future, so search for some keywords in the file name.
        """
        return [
            path
            for path in paths_to_docx_files
            if "AHB" in path.name
            or "MIG" in path.name
            or "AllgemeineFestlegungen" in path.name
            or "Codeliste" in path.name
            or "Entscheidungsbaum" in path.name
        ]

    # pylint: disable=line-too-long
    @staticmethod
    def group_files_by_name_prefix(paths_to_docx_files: list[Path]) -> dict[str, list[Path]]:
        """
        This function groups the docx files by their name prefix.
        Groups may now look like this:
        {'APERAKCONTRLAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/APERAKCONTRLAHB-informatorischeLesefassung2.3m_99991231_20231001.docx')],
         'COMDISAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/COMDISAHB-informatorischeLesefassung1.0dKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/COMDISAHB-informatorischeLesefassung1.0d_99991231_20231001.docx')],
         'HerkunftsnachweisregisterAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/HerkunftsnachweisregisterAHB-informatorischeLesefassung2.3cKonsolidierteLesefassungmitFehlerkorrekturenStand19.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/HerkunftsnachweisregisterAHB-informatorischeLesefassung2.3c_99991231_20231001.docx')],
         'IFTSTAAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/IFTSTAAHB-informatorischeLesefassung2.0eKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/IFTSTAAHB-informatorischeLesefassung2.0e_99991231_20231001.docx')],
         'INVOICREMADVAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/INVOICREMADVAHB-informatorischeLesefassung2.5bKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/INVOICREMADVAHB-informatorischeLesefassung2.5b_99991231_20231001.docx')],
         'MSCONSAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/MSCONSAHB-informatorischeLesefassung3.1c_99991231_20231001.docx')],
         'ORDERSORDRSPAHBMaBiS': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/ORDERSORDRSPAHBMaBiS-informatorischeLesefassung2.2c_99991231_20231001.docx')],
         'PARTINAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/PARTINAHB-informatorischeLesefassung1.0c_99991231_20231001.docx')],
         'PRICATAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/PRICATAHB-informatorischeLesefassung2.0c_99991231_20231001.docx')],
         'REQOTEQUOTESORDERSORDRSPORDCHGAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/REQOTEQUOTESORDERSORDRSPORDCHGAHB-informatorischeLesefassung2.2KonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/REQOTEQUOTESORDERSORDRSPORDCHGAHB-informatorischeLesefassung2.2_99991231_20231001.docx')],
         'UTILMDAHBGas': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBGas-informatorischeLesefassung1.0aKonsolidierteLesefassungmitFehlerkorrekturenStand29.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBGas-informatorischeLesefassung1.0a_99991231_20231001.docx')],
         'UTILMDAHBMaBiS': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBMaBiS-informatorischeLesefassung4.1_99991231_20231001.docx')],
         'UTILMDAHBStrom': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBStrom-informatorischeLesefassung1.1KonsolidierteLesefassungmitFehlerkorrekturenStand29.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBStrom-informatorischeLesefassung1.1_99991231_20231001.docx')],
         'UTILTSAHBBerechnungsformel': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILTSAHBBerechnungsformel-informatorischeLesefassung1.0e_99991231_20231001.docx')], 'UTILTSAHBDefinitionen': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILTSAHBDefinitionen-informatorischeLesefassung1.1_99991231_20231001.docx')]}
        """
        return {
            group_key: list(group)
            for group_key, group in groupby(
                sorted(paths_to_docx_files, key=DocxFileFinder.get_first_part_of_ahb_docx_file_name),
                key=DocxFileFinder.get_first_part_of_ahb_docx_file_name,
            )
        }

    @staticmethod
    def filter_latest_version(groups: dict[str, list[Path]]) -> list[Path]:
        """
        Filters and returns the latest version of the AHB or MIG .docx files
        from the provided groups based on specific criteria.

        The latest version is determined based on the presence of specific
        keywords in the filename and the numerical suffix in the filename.

        Parameters:
        - groups (Dict[str, List[Path]]): A dictionary where keys are group identifiers
        and values are lists of Path objects representing the file paths.

        Returns:
        - List[Path]: A list of Path objects representing the latest version of the files.
        """
        result: list[Path] = []

        for group_items in groups.values():
            if len(group_items) == 1:
                result.append(group_items[0])
            else:
                try:

                    list_of_edi_energy_documents = [EdiEnergyDocument.from_path(path) for path in group_items]

                    # sort list to get easy to read log messages
                    list_of_edi_energy_documents.sort()
                    most_recent_file_name = last(list_of_edi_energy_documents).filename

                    # Add the most recent file to the result and log ignored files
                    for path in group_items:
                        if path != most_recent_file_name:
                            logger.debug("Ignoring file %s", path.name)
                        else:
                            logger.info("Will read file %s", path.name)
                            result.append(most_recent_file_name)

                except ValueError as e:
                    logger.error("Error processing group items: %s", e)
                    continue

        return result

    def filter_for_latest_mig_and_ahb_docx_files(self) -> None:
        """
        Filter the list of MIG docx paths for the latest MIG docx files.
        """
        self.paths_to_docx_files = self.filter_for_docx_files_with_change_history(self.paths_to_docx_files)
        grouped_files = self.group_files_by_name_prefix(self.paths_to_docx_files)
        self.paths_to_docx_files = self.filter_latest_version(grouped_files)

    def filter_docx_files_for_edifact_format(self, edifact_format: EdifactFormat) -> None:
        """
        Returns a list of docx files which contain the given edifact format.
        This method is not pure. It changes the state of the object.
        """

        self.paths_to_docx_files = [path for path in self.paths_to_docx_files if str(edifact_format) in path.name]

    def remove_temporary_files(self) -> None:
        """
        This method removes all temporary files from paths_to_docx_files.
        Temporary files lead to the exception `BadZipFile: File is not a zip file`.
        It appears if a docx file is opened by Word.
        """

        self.paths_to_docx_files = [path for path in self.paths_to_docx_files if not path.name.startswith("~")]

    def get_docx_files_which_may_contain_searched_pruefi(self, searched_pruefi: str) -> list[Path]:
        """
        This functions takes a pruefidentifikator and returns a list of docx files which can contain the searched pruefi
        Unfortunately, it is not clear in which docx the pruefidentifikator you are looking for is located.
        A 11042 belongs to the UTILMD format. However, there are seven docx files that describe the UTILMD format.
        A further reduction of the number of files is not possible with the pruefidentifikator only.
        This method is _not_ pure. It changes the state of the object.
        """

        edifact_format = get_format_of_pruefidentifikator(searched_pruefi)
        if edifact_format is None:
            logger.exception("❌ There is no known format for the prüfi '%s'.", searched_pruefi)
            raise ValueError(f"There is no known format for the prüfi '{searched_pruefi}'.")

        self.filter_for_latest_ahb_docx_files()
        self.filter_docx_files_for_edifact_format(edifact_format=edifact_format)
        if (
            edifact_format == EdifactFormat.UTILMD
            and searched_pruefi.startswith("11")
            and all("202310" in path.name for path in self.paths_to_docx_files)
        ):
            logger.info(
                # pylint:disable=line-too-long
                "You searched for a UTILMD prüfi %s starting with the soon deprecated prefix '11' but all relevant files %s are valid from 2023-10 onwards. They won't contain any match.",
                searched_pruefi,
                ", ".join([path.name for path in self.paths_to_docx_files]),
            )
            return []
        return self.paths_to_docx_files

    def get_all_docx_files_which_contain_change_histories(self) -> list[Path]:
        """
        This function returns a list of docx files which probably contain a change history.
        Only format documents like UTILMD, MSCONS etc. contain a change history.
        """

        self.filter_for_latest_mig_and_ahb_docx_files()
        self.remove_temporary_files()

        return self.paths_to_docx_files

    def get_docx_files_which_contain_quality_map(self) -> list[Path]:
        """
        This function returns a list of docx files which contain a quality map.
        """

        self.filter_for_latest_ahb_docx_files()
        self.remove_temporary_files()

        indicator_string = "UTILMDAHBStrom"
        self.paths_to_docx_files = [path for path in self.paths_to_docx_files if indicator_string in path.name]

        return self.paths_to_docx_files
