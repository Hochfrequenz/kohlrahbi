"""
This module contains the DocxFileFinder class.
"""

import re
from itertools import groupby
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
        # assert document_metadata.version is not None, "Document version is None."

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

    def get_file_paths_for_change_history(self, format_version: EdifactFormatVersion):
        # first I need to filter for the docx files.

        path_to_format_version: Path = self.path_to_edi_energy_mirror / format_version.value
        assert (
            path_to_format_version.exists()
        ), f"The path to the format version {path_to_format_version} does not exist."
        assert (
            path_to_format_version.is_dir()
        ), f"The path to the format version {format_version.value} is not a directory."

        temporary_files: list[Path] = []

        for path in path_to_format_version.iterdir():
            if path.name.startswith("~") or not path.name.endswith(".docx"):
                # skip temporary files and non-docx files
                continue
            document_metadata = extract_document_meta_data(path.name)
            is_document_informational_reading_version = (
                document_metadata is not None and document_metadata.is_informational_reading_version
            )
            if is_document_informational_reading_version:
                temporary_files.append(path)

        groups = self.group_documents_by_kind_and_format(temporary_files)

        for group in groups.values():
            if len(group) == 1:
                # self.result_paths.append(group[0])
                continue
            else:
                # iterate over the group
                for path in group:
                    # get the document metadata
                    document_metadata = extract_document_meta_data(path.name)
                    if document_metadata is None:
                        continue
                    # sort the group by document_metadata.version, document_metadata.publication_date, document_metadata.valid_from, document_metadata.to_date
                    try:
                        # First check if any document in the group has error corrections
                        has_error_correction = any(
                            extract_document_meta_data(x.name).is_error_correction for x in group
                        )

                        # If we have error corrections, filter out non-error-correction documents
                        if has_error_correction:
                            group[:] = [x for x in group if extract_document_meta_data(x.name).is_error_correction]

                        group.sort(
                            key=lambda x: (
                                extract_document_meta_data(x.name).version,
                                extract_document_meta_data(x.name).publication_date,
                                extract_document_meta_data(x.name).valid_from,
                                extract_document_meta_data(x.name).valid_until,
                            ),
                            reverse=True,  # we want the latest version first
                        )
                    except TypeError:
                        logger.exception("Could not sort the group %s", group)

        for group in groups.values():
            self.result_paths.append(group[0])

        return sorted(self.result_paths)

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
        self.path_to_edi_energy_mirror = self.filter_ahb_docx_files(self.path_to_edi_energy_mirror)
        grouped_files = self.group_files_by_name_prefix(self.path_to_edi_energy_mirror)
        self.path_to_edi_energy_mirror = self.filter_latest_version(grouped_files)

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
            if "ahb" in path.name.lower()
            or "mig" in path.name.lower()
            or "allgemeinefestlegungen" in path.name.lower()
            or "apiguideline" in path.name.lower()
            or "codeliste" in path.name.lower()
            or "ebd" in path.name.lower()
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
            most_recent_file = get_most_recent_file(group_items)
            assert most_recent_file is not None, "Could not find the most recent file."
            result.append(most_recent_file)
        return result

    def filter_for_latest_mig_and_ahb_docx_files(self) -> None:
        """
        Filter the list of MIG docx paths for the latest MIG docx files.
        """
        self.path_to_edi_energy_mirror = self.filter_for_docx_files_with_change_history(self.path_to_edi_energy_mirror)
        grouped_files = self.group_files_by_name_prefix(self.path_to_edi_energy_mirror)
        self.path_to_edi_energy_mirror = self.filter_latest_version(grouped_files)

    def filter_docx_files_for_edifact_format(self, edifact_format: EdifactFormat) -> None:
        """
        Returns a list of docx files which contain the given edifact format.
        This method is not pure. It changes the state of the object.
        """

        self.path_to_edi_energy_mirror = [
            path for path in self.path_to_edi_energy_mirror if str(edifact_format) in path.name
        ]

    def remove_temporary_files(self) -> None:
        """
        This method removes all temporary files from paths_to_docx_files.
        Temporary files lead to the exception `BadZipFile: File is not a zip file`.
        It appears if a docx file is opened by Word.
        """

        self.path_to_edi_energy_mirror = [
            path for path in self.path_to_edi_energy_mirror if not path.name.startswith("~")
        ]

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

    def get_all_docx_files_which_contain_change_histories(self) -> list[Path]:
        """
        This function returns a list of docx files which probably contain a change history.
        Only format documents like UTILMD, MSCONS etc. contain a change history.
        """

        # self.paths_to_docx_files = self.filter_for_docx_files_with_change_history(self.paths_to_docx_files)

        # self.filter_for_latest_mig_and_ahb_docx_files()
        self.remove_temporary_files()

        paths_to_relevant_docx_files = []
        for path in self.path_to_edi_energy_mirror:
            document_metadata = extract_document_meta_data(path.name)
            is_document_relevant = document_metadata is not None and (
                document_metadata.is_informational_reading_version
                and document_metadata.is_consolidated_reading_version
                and document_metadata.is_error_correction
            )
            if is_document_relevant:
                paths_to_relevant_docx_files.append(path)

        self.path_to_edi_energy_mirror = paths_to_relevant_docx_files
        return self.path_to_edi_energy_mirror

    def get_docx_files_which_contain_quality_map(self) -> list[Path]:
        """
        This function returns a list of docx files which contain a quality map.
        """

        self.filter_for_latest_ahb_docx_files()
        self.remove_temporary_files()

        indicator_string = "UTILMDAHBStrom"
        self.path_to_edi_energy_mirror = [
            path for path in self.path_to_edi_energy_mirror if indicator_string in path.name
        ]

        return self.path_to_edi_energy_mirror

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
