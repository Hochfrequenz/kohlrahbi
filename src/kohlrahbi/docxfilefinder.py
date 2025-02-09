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

    format_version: EdifactFormatVersion

    result_paths: list[Path] = []

    @property
    def path_to_format_version_folders(self):
        """Returns the path to the edi_energy_de directory containing format version folders like FV2410, FV2404, etc."""
        path_to_edi_energy_mirror = self.path_to_edi_energy_mirror
        if not path_to_edi_energy_mirror.exists():
            raise ValueError(f"The edi_energy_mirror directory {path_to_edi_energy_mirror} does not exist.")
        return path_to_edi_energy_mirror / Path("edi_energy_de")

    @property
    def path_to_specific_format_version_folder(self):
        """Returns the path to the specific format version folder."""
        specific_format_version_folder = self.path_to_format_version_folders / Path(self.format_version.value)
        if not specific_format_version_folder.exists():
            raise ValueError(f"The specific format version folder {specific_format_version_folder} does not exist.")
        return specific_format_version_folder

    def get_file_paths_for_change_history(self) -> list[Path]:
        """Get all file paths that contain change history for a given format version."""

        self._get_valid_docx_files()
        self._filter_informational_versions()
        self._get_most_recent_versions()

        return self.result_paths

    def get_file_paths_for_ahbs(self) -> list[Path]:
        """Get all AHB file paths for a given format version."""

        self._get_valid_docx_files()
        self._filter_informational_versions()
        self._filter_for_ahb_docx_files()
        self._get_most_recent_versions()

        return self.result_paths

    def _filter_for_ahb_docx_files(self) -> None:
        """Filter the list of AHB docx paths for the latest AHB docx files.

        The latest files contain `LesefassungmitFehlerkorrekturen` in their file names.
        """
        self.result_paths = [path for path in self.result_paths if "AHB" in path.name]

    def _get_valid_docx_files(self) -> None:
        """Get all valid docx files from a directory, excluding temporary files.

        Args:
            directory (Path): The directory to search in.

        Returns:
            list[Path]: A list of paths to valid docx files.
        """
        self.result_paths = [
            path
            for path in self.path_to_specific_format_version_folder.iterdir()
            if path.name.endswith(".docx") and not path.name.startswith("~")
        ]

    def _filter_informational_versions(self) -> None:
        """Filter paths to only include informational reading versions.

        Args:
            paths (list[Path]): List of paths to filter.

        Returns:
            list[Path]: Filtered list containing only informational reading versions.
        """
        informational_versions = []
        for path in self.result_paths:
            document_metadata = extract_document_meta_data(path.name)
            if document_metadata and document_metadata.is_informational_reading_version:
                informational_versions.append(path)
        self.result_paths = informational_versions

    def _get_most_recent_versions(self) -> None:
        """Get the most recent version from each group of documents.

        Args:
            grouped_docs (dict[tuple[str, str], list[Path]]): Documents grouped by kind and format.

        Returns:
            list[Path]: List of the most recent version from each group.
        """

        grouped_docs = self.group_documents_by_kind_and_format(self.result_paths)

        most_recent_versions = []
        for group in grouped_docs.values():
            if len(group) == 1:
                most_recent_versions.append(group[0])
                continue

            filtered_group = self._filter_error_corrections(group)
            sorted_group = self._sort_group_by_metadata(filtered_group)
            if sorted_group:
                most_recent_versions.append(sorted_group[0])

        self.result_paths = sorted(most_recent_versions)

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
                        extract_document_meta_data(x.name).is_extraordinary_publication,
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

    def _filter_docx_files_for_edifact_format(self, edifact_format: EdifactFormat) -> None:
        """
        Filters the result_paths to only include files containing the given EDIFACT format in their name.

        This method modifies the state of the object by updating result_paths.

        Args:
            edifact_format (EdifactFormat): The EDIFACT format to filter for (e.g. UTILMD, MSCONS)

        Returns:
            None
        """

        self.result_paths = [path for path in self.result_paths if str(edifact_format) in path.name]

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
