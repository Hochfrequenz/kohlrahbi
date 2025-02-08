"""
This module contains the DocxFileFinder class.
"""

import re
from pathlib import Path

from edi_energy_scraper import DocumentMetadata
from efoli import EdifactFormat, EdifactFormatVersion, get_format_of_pruefidentifikator
from pydantic import BaseModel

from kohlrahbi.logger import logger


class EdiEnergyDocument(BaseModel):
    """
    This class represents an EDI Energy document.
    """

    filename: Path
    document_version: str
    version_prefix: str
    version_major: int
    version_minor: int
    version_suffix: str
    valid_from: int
    valid_until: int

    @classmethod
    def from_path(cls, path: Path) -> "EdiEnergyDocument":
        """
        Create an EdiEnergyDocument object from a file path.
        """

        document_metadata = extract_document_meta_data(path.name)
        assert document_metadata is not None, f"Could not extract document version and valid dates from {path.name}."
        assert document_metadata.version is not None, "Document version is None."

        prefix, version_major, version_minor, version_suffix = split_version_string(document_metadata.version)

        valid_from = int(document_metadata.valid_from.strftime("%Y%m%d"))
        valid_until = int(document_metadata.valid_until.strftime("%Y%m%d"))
        # assert valid_from <= valid_until, "Valid from is greater than valid until."
        assert isinstance(valid_from, int), "Valid from is not an integer."
        assert isinstance(valid_until, int), "Valid until is not an integer."

        return cls(
            filename=path,
            document_version=document_metadata.version,
            version_prefix=prefix,
            version_major=version_major,
            version_minor=version_minor,
            version_suffix=version_suffix,
            valid_from=valid_from,
            valid_until=valid_until,
        )

    def __lt__(self, other: "EdiEnergyDocument") -> bool:
        """
        Compare two EdiEnergyDocument instances based on
        their document_version(major, minor and suffix), valid_until, and valid_from.

        I did not know how the tuple comparison works in Python, so I looked it up:

        Python compares tuples lexicographically, meaning it compares the elements one by one from left to right.
        The comparison starts with the first elements of both tuples:
          If self.valid_from is less than other.valid_from, the entire expression evaluates to True.
          If self.valid_from is greater than other.valid_from, the entire expression evaluates to False.
          If self.valid_from is equal to other.valid_from, Python moves to the next elements in the tuples.
        This process continues with self.valid_until vs. other.valid_until and then with the version numbers.

        Args:
            other (EdiEnergyDocument): The other document to compare against.

        Returns:
            bool: True if this document is considered less than the other document, False otherwise.
        """
        return (self.valid_from, self.valid_until, self.version_major, self.version_minor, self.version_suffix) < (
            other.valid_from,
            other.valid_until,
            other.version_major,
            other.version_minor,
            other.version_suffix,
        )


def split_version_string(version_string: str) -> tuple[str, int, int, str]:
    """
    Split the version string into a tuple of (prefix, major, minor, suffix).
    The prefix is optional (can be empty string).

    Examples:
        >>> split_version_string("1.3a")
        ('', 1, 3, 'a')
        >>> split_version_string("G2.1e")
        ('G', 2, 1, 'e')
        >>> split_version_string("S1.2f")
        ('S', 1, 2, 'f')
    """
    pattern = r"^([GS])?(\d+)\.(\d+)([a-zA-Z]*)$"
    match = re.match(pattern, version_string)
    if not match:
        raise ValueError(f"Invalid version string format: {version_string}")

    prefix, major, minor, suffix = match.groups()
    return (
        prefix or "",  # convert None to empty string if no prefix
        int(major),
        int(minor),
        suffix or "",  # convert None to empty string if no suffix
    )


def extract_document_meta_data(
    filename: str,
) -> DocumentMetadata:
    """Extract the document metadata from the filename.

    Parameters:
    - filename (str): The filename of the document.

    Returns:
    - DocumentMetadata: A DocumentMetadata object.
    """

    document_metadata = DocumentMetadata.from_filename(filename)
    assert document_metadata is not None, f"Could not extract document metadata from {filename}."
    return document_metadata


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
        # keywords = ["konsolidiertelesefassungmitfehlerkorrekturen", "außerordentlicheveröffentlichung"]
        # ahb_and_mig_file_paths = [
        #     path for path in group_items if path.name.lower().startswith("ahb") or path.name.lower().startswith("mig")
        # ]

        ahb_and_mig_file_paths = []
        for path in group_items:
            document_metadata = extract_document_meta_data(path.name)
            is_document_relevant = document_metadata is not None and (
                document_metadata.is_informational_reading_version
                and document_metadata.is_consolidated_reading_version
                and document_metadata.is_error_correction
            )
            if is_document_relevant:
                ahb_and_mig_file_paths.append(path)

        # assert len(ahb_and_mig_file_paths) > 0, "No AHB or MIG files found."

        list_of_edi_energy_documents = [EdiEnergyDocument.from_path(path) for path in ahb_and_mig_file_paths]

        # assert len(list_of_edi_energy_documents) > 0, "No AHB files found."
        most_recent_file = max(list_of_edi_energy_documents)

        # assert most_recent_file is not None, "Most recent file is None."

        return most_recent_file.filename

    except ValueError as e:

        logger.error("Error processing group items: %s", e)
    return None


class DocxFileFinder(BaseModel):
    """
    This class is responsible for finding the correct docx files in the edi energy mirror.
    It is used for all commands which need to find docx files.
    """

    path_to_edi_energy_mirror: Path

    result_paths: list[Path] = []

    @property
    def path_to_format_version_folders(self):
        return self.path_to_edi_energy_mirror / Path("edi_energy_de")

    def get_file_paths_for_change_history(self, format_version: EdifactFormatVersion) -> list[Path]:
        """Get all file paths that contain change history for a given format version.

        This method finds all docx files in the format version directory that are informational reading versions,
        groups them by document type, and returns the most recent version of each document.

        Args:
            format_version (EdifactFormatVersion): The EDIFACT format version to search in.

        Returns:
            list[Path]: A list of paths to the most recent version of each document.

        Raises:
            ValueError: If the format version directory does not exist or is not a directory.
        """
        format_version_path = self._get_validated_format_version_path(format_version)
        docx_files = self._get_valid_docx_files(format_version_path)
        informational_versions = self._filter_informational_versions(docx_files)
        grouped_docs = self.group_documents_by_kind_and_format(informational_versions)

        return self._get_most_recent_versions(grouped_docs)

    def get_file_paths_for_ahbs(self, format_version: EdifactFormatVersion) -> list[Path]:
        """Get all AHB file paths for a given format version.

        This method finds all AHB docx files in the format version directory that are informational reading versions,
        groups them by document type, and returns the most recent version of each document.

        Args:
            format_version (EdifactFormatVersion): The EDIFACT format version to search in.

        Returns:
            list[Path]: A list of paths to the most recent version of each AHB document.

        Raises:
            ValueError: If the format version directory does not exist or is not a directory.
        """
        format_version_path = self._get_validated_format_version_path(format_version)
        docx_files = self._get_valid_docx_files(format_version_path)
        informational_versions = self._filter_informational_versions(docx_files)

        # Filter for AHB files only
        ahb_files = [path for path in informational_versions if "AHB" in path.name]
        grouped_docs = self.group_documents_by_kind_and_format(ahb_files)

        return self._get_most_recent_versions(grouped_docs)

    def _get_validated_format_version_path(self, format_version: EdifactFormatVersion) -> Path:
        """Validate and return the path for a given format version.

        Args:
            format_version (EdifactFormatVersion): The format version to get the path for.

        Returns:
            Path: The validated path to the format version directory.

        Raises:
            ValueError: If the path does not exist or is not a directory.
        """
        version_path = self.path_to_edi_energy_mirror / format_version.value
        if not version_path.exists():
            raise ValueError(f"Format version directory does not exist: {version_path}")
        if not version_path.is_dir():
            raise ValueError(f"Format version path is not a directory: {version_path}")
        return version_path

    def _get_valid_docx_files(self, directory: Path) -> list[Path]:
        """Get all valid docx files from a directory, excluding temporary files.

        Args:
            directory (Path): The directory to search in.

        Returns:
            list[Path]: A list of paths to valid docx files.
        """
        return [path for path in directory.iterdir() if path.name.endswith(".docx") and not path.name.startswith("~")]

    def _filter_informational_versions(self, paths: list[Path]) -> list[Path]:
        """Filter paths to only include informational reading versions.

        Args:
            paths (list[Path]): List of paths to filter.

        Returns:
            list[Path]: Filtered list containing only informational reading versions.
        """
        informational_versions = []
        for path in paths:
            document_metadata = extract_document_meta_data(path.name)
            if document_metadata and document_metadata.is_informational_reading_version:
                informational_versions.append(path)
        return informational_versions

    def _get_most_recent_versions(self, grouped_docs: dict[tuple[str, str], list[Path]]) -> list[Path]:
        """Get the most recent version from each group of documents.

        Args:
            grouped_docs (dict[tuple[str, str], list[Path]]): Documents grouped by kind and format.

        Returns:
            list[Path]: List of the most recent version from each group.
        """
        most_recent_versions = []
        for group in grouped_docs.values():
            if len(group) == 1:
                most_recent_versions.append(group[0])
                continue

            filtered_group = self._filter_error_corrections(group)
            sorted_group = self._sort_group_by_metadata(filtered_group)
            if sorted_group:
                most_recent_versions.append(sorted_group[0])

        return sorted(most_recent_versions)

    def _filter_error_corrections(self, group: list[Path]) -> list[Path]:
        """Filter group to keep only error correction versions if they exist.

        Args:
            group (list[Path]): List of paths in a group.

        Returns:
            list[Path]: Filtered list containing only error correction versions if they exist,
                       otherwise returns the original group.
        """
        has_error_correction = any(
            extract_document_meta_data(path.name).is_error_correction
            for path in group
            if extract_document_meta_data(path.name)
        )

        if has_error_correction:
            return [
                path
                for path in group
                if extract_document_meta_data(path.name) and extract_document_meta_data(path.name).is_error_correction
            ]
        return group

    def _sort_group_by_metadata(self, group: list[Path]) -> list[Path]:
        """Sort group by version, publication date, and validity dates.

        Args:
            group (list[Path]): List of paths to sort.

        Returns:
            list[Path]: Sorted list of paths.
        """
        try:
            return sorted(
                group,
                key=lambda x: (
                    (
                        extract_document_meta_data(x.name).version,
                        extract_document_meta_data(x.name).publication_date,
                        extract_document_meta_data(x.name).valid_from,
                        extract_document_meta_data(x.name).valid_until,
                    )
                    if extract_document_meta_data(x.name)
                    else (None, None, None, None)
                ),
                reverse=True,
            )
        except TypeError as e:
            logger.exception("Could not sort group %s: %s", group, e)
            return group

    @staticmethod
    def get_first_part_of_ahb_docx_file_name(path_to_ahb_document: Path) -> str:
        """
        Return the first part of the AHB docx file name.
        The first part contains the information about the EDIFACT formats.
        """

        return path_to_ahb_document.name.split("-")[0]

    # def filter_for_latest_ahb_docx_files(self) -> None:
    #     """
    #     Filter the list of AHB docx paths for the latest AHB docx files.
    #     The latest files contain `LesefassungmitFehlerkorrekturen` in their file names.
    #     This method is _not_ pure. It changes the state of the object.
    #     """
    #     self.path_to_edi_energy_mirror = self.filter_ahb_docx_files(self.path_to_edi_energy_mirror)
    #     grouped_files = self.group_files_by_name_prefix(self.path_to_edi_energy_mirror)
    #     self.path_to_edi_energy_mirror = self.filter_latest_version(grouped_files)

    # @staticmethod
    # def filter_ahb_docx_files(paths_to_docx_files: list[Path]) -> list[Path]:
    #     """
    #     This function filters the docx files which contain the string "AHB" in their file name.
    #     """
    #     return [path for path in paths_to_docx_files if "AHB" in path.name]

    # pylint: disable=line-too-long
    # @staticmethod
    # def group_files_by_name_prefix(paths_to_docx_files: list[Path]) -> dict[str, list[Path]]:
    #     """
    #     This function groups the docx files by their name prefix.
    #     Groups may now look like this:
    #     {'APERAKCONTRLAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/APERAKCONTRLAHB-informatorischeLesefassung2.3m_99991231_20231001.docx')],
    #      'COMDISAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/COMDISAHB-informatorischeLesefassung1.0dKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/COMDISAHB-informatorischeLesefassung1.0d_99991231_20231001.docx')],
    #      'HerkunftsnachweisregisterAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/HerkunftsnachweisregisterAHB-informatorischeLesefassung2.3cKonsolidierteLesefassungmitFehlerkorrekturenStand19.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/HerkunftsnachweisregisterAHB-informatorischeLesefassung2.3c_99991231_20231001.docx')],
    #      'IFTSTAAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/IFTSTAAHB-informatorischeLesefassung2.0eKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/IFTSTAAHB-informatorischeLesefassung2.0e_99991231_20231001.docx')],
    #      'INVOICREMADVAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/INVOICREMADVAHB-informatorischeLesefassung2.5bKonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/INVOICREMADVAHB-informatorischeLesefassung2.5b_99991231_20231001.docx')],
    #      'MSCONSAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/MSCONSAHB-informatorischeLesefassung3.1c_99991231_20231001.docx')],
    #      'ORDERSORDRSPAHBMaBiS': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/ORDERSORDRSPAHBMaBiS-informatorischeLesefassung2.2c_99991231_20231001.docx')],
    #      'PARTINAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/PARTINAHB-informatorischeLesefassung1.0c_99991231_20231001.docx')],
    #      'PRICATAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/PRICATAHB-informatorischeLesefassung2.0c_99991231_20231001.docx')],
    #      'REQOTEQUOTESORDERSORDRSPORDCHGAHB': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/REQOTEQUOTESORDERSORDRSPORDCHGAHB-informatorischeLesefassung2.2KonsolidierteLesefassungmitFehlerkorrekturenStand20.07.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/REQOTEQUOTESORDERSORDRSPORDCHGAHB-informatorischeLesefassung2.2_99991231_20231001.docx')],
    #      'UTILMDAHBGas': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBGas-informatorischeLesefassung1.0aKonsolidierteLesefassungmitFehlerkorrekturenStand29.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBGas-informatorischeLesefassung1.0a_99991231_20231001.docx')],
    #      'UTILMDAHBMaBiS': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBMaBiS-informatorischeLesefassung4.1_99991231_20231001.docx')],
    #      'UTILMDAHBStrom': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBStrom-informatorischeLesefassung1.1KonsolidierteLesefassungmitFehlerkorrekturenStand29.06.2023_99991231_20231001.docx'), WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILMDAHBStrom-informatorischeLesefassung1.1_99991231_20231001.docx')],
    #      'UTILTSAHBBerechnungsformel': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILTSAHBBerechnungsformel-informatorischeLesefassung1.0e_99991231_20231001.docx')], 'UTILTSAHBDefinitionen': [WindowsPath('../edi_energy_mirror/edi_energy_de/future/UTILTSAHBDefinitionen-informatorischeLesefassung1.1_99991231_20231001.docx')]}
    #     """
    #     return {
    #         group_key: list(group)
    #         for group_key, group in groupby(
    #             sorted(paths_to_docx_files, key=DocxFileFinder.get_first_part_of_ahb_docx_file_name),
    #             key=DocxFileFinder.get_first_part_of_ahb_docx_file_name,
    #         )
    #     }

    # @staticmethod
    # def filter_latest_version(groups: dict[str, list[Path]]) -> list[Path]:
    #     """
    #     Filters and returns the latest version of the AHB or MIG .docx files
    #     from the provided groups based on specific criteria.

    #     The latest version is determined based on the presence of specific
    #     keywords in the filename and the numerical suffix in the filename.

    #     Parameters:
    #     - groups (Dict[str, List[Path]]): A dictionary where keys are group identifiers
    #     and values are lists of Path objects representing the file paths.

    #     Returns:
    #     - List[Path]: A list of Path objects representing the latest version of the files.
    #     """
    #     result: list[Path] = []

    #     for group_items in groups.values():
    #         most_recent_file = get_most_recent_file(group_items)
    #         assert most_recent_file is not None, "Could not find the most recent file."
    #         result.append(most_recent_file)
    #     return result

    # def filter_docx_files_for_edifact_format(self, edifact_format: EdifactFormat) -> None:
    #     """
    #     Returns a list of docx files which contain the given edifact format.
    #     This method is not pure. It changes the state of the object.
    #     """

    #     self.path_to_edi_energy_mirror = [
    #         path for path in self.path_to_edi_energy_mirror if str(edifact_format) in path.name
    #     ]

    # def remove_temporary_files(self) -> None:
    #     """
    #     This method removes all temporary files from paths_to_docx_files.
    #     Temporary files lead to the exception `BadZipFile: File is not a zip file`.
    #     It appears if a docx file is opened by Word.
    #     """

    #     self.path_to_edi_energy_mirror = [
    #         path for path in self.path_to_edi_energy_mirror if not path.name.startswith("~")
    #     ]

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
            and all("202310" in path.name for path in self.path_to_edi_energy_mirror)
        ):
            logger.info(
                # pylint:disable=line-too-long
                "You searched for a UTILMD prüfi %s starting with the soon deprecated prefix '11' but all relevant files %s are valid from 2023-10 onwards. They won't contain any match.",
                searched_pruefi,
                ", ".join([path.name for path in self.path_to_edi_energy_mirror]),
            )
            return []
        return self.path_to_edi_energy_mirror

    # def get_all_docx_files_which_contain_change_histories(self) -> list[Path]:
    #     """
    #     This function returns a list of docx files which probably contain a change history.
    #     Only format documents like UTILMD, MSCONS etc. contain a change history.
    #     """

    #     # self.paths_to_docx_files = self.filter_for_docx_files_with_change_history(self.paths_to_docx_files)

    #     # self.filter_for_latest_mig_and_ahb_docx_files()
    #     self.remove_temporary_files()

    #     paths_to_relevant_docx_files = []
    #     for path in self.path_to_edi_energy_mirror:
    #         document_metadata = extract_document_meta_data(path.name)
    #         is_document_relevant = document_metadata is not None and (
    #             document_metadata.is_informational_reading_version
    #             and document_metadata.is_consolidated_reading_version
    #             and document_metadata.is_error_correction
    #         )
    #         if is_document_relevant:
    #             paths_to_relevant_docx_files.append(path)

    #     self.path_to_edi_energy_mirror = paths_to_relevant_docx_files
    #     return self.path_to_edi_energy_mirror

    def get_docx_files_which_contain_quality_map(self) -> list[Path]:
        """
        This function returns a list of docx files which contain a quality map.
        Only the UTILMD AHB Strom documents contain quality maps.

        Returns:
            list[Path]: A list of paths to the most recent UTILMD AHB Strom documents.
        """
        # Get all docx files in the directory
        docx_files = self._get_valid_docx_files(self.path_to_edi_energy_mirror)

        # Filter for informational versions
        informational_versions = self._filter_informational_versions(docx_files)

        # Group documents by kind and format
        grouped_docs = self.group_documents_by_kind_and_format(informational_versions)

        # Find the UTILMD AHB Strom group
        utilmd_strom_docs = []
        for group_key, group_paths in grouped_docs.items():
            if any("UTILMDAHBStrom" in path.name for path in group_paths):
                utilmd_strom_docs.extend(group_paths)

        if not utilmd_strom_docs:
            return []

        # Get the most recent version
        most_recent = get_most_recent_file(utilmd_strom_docs)
        return [most_recent] if most_recent else []

    @staticmethod
    def group_documents_by_kind_and_format(paths: list[Path]) -> dict[tuple[str, str], list[Path]]:
        """
        Groups documents by their kind and EDIFACT format.

        Args:
            paths (list[Path]): List of paths to process

        Returns:
            dict[tuple[str, str], list[Path]]: Dictionary where key is (kind, edifact_format) and value is list of paths

        Example:
            >>> paths = [Path("UTILMDAHB-1.0.docx"), Path("INVOICAHB-2.0.docx")]
            >>> result = DocxFileFinder.group_documents_by_format(paths)
            >>> # Result might look like: {("AHB", "UTILMD"): [Path("UTILMDAHB-1.0.docx")],
            >>> #                         ("AHB", "INVOIC"): [Path("INVOICAHB-2.0.docx")]}
        """
        result: dict[tuple[str, str], list[Path]] = {}

        for path in paths:
            try:
                metadata = extract_document_meta_data(path.name)
                if metadata is None or metadata.kind is None or metadata.edifact_format is None:

                    # cases for
                    # 'codelistederkonfigurationen_1.3b_20250606_99991231_20241213_xoxx_11124.docx'
                    # 'codelistederkonfigurationeninformatorischelesefassung_1.3b_20250606_99991231_20250606_ooox_8757.docx'
                    # 'allgemeinefestlegungeninformatorischelesefassung_6.1b_20250606_99991231_20250606_ooox_8638.docx'
                    # 'apiguidelineinformatorischelesefassung_1.0a_20250606_99991231_20250606_ooox_10824.docx'

                    x = path.name.split("_")[0]

                    key = (x, "")

                else:
                    key = (metadata.kind, metadata.edifact_format)
                if key not in result:
                    result[key] = []
                result[key].append(path)
            except Exception as e:
                logger.warning(f"Could not process {path.name}: {str(e)}")
                continue

        return result
