"""
This module contains the AhbFileFinder class.
"""
from itertools import groupby
from pathlib import Path

import attrs
from maus.edifact import EdifactFormat, get_format_of_pruefidentifikator

from kohlrahbi.logger import logger


@attrs.define(auto_attribs=True, kw_only=True)
class AhbFileFinder:
    """
    This class is responsible for finding the AHB files in the input directory.
    """

    paths_to_docx_files: list[Path]

    @classmethod
    def from_input_path(cls, input_path: Path) -> "AhbFileFinder":
        """
        Create an AhbFileFinder object from the input path.
        """

        ahb_file_paths: list[Path] = [
            path for path in input_path.iterdir() if path.is_file() if path.suffix == ".docx" if "AHB" in path.name
        ]
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
        """
        result: list[Path] = []

        groups: dict[str, list[Path]] = {}  # the key is the first part of the file name, the values are matching files

        for key, group in groupby(
            sorted(self.paths_to_docx_files, key=AhbFileFinder.get_first_part_of_ahb_docx_file_name),
            AhbFileFinder.get_first_part_of_ahb_docx_file_name,
        ):
            groups[key] = list(group)

        for group_items in groups.values():
            if len(group_items) == 1:
                result.append(group_items[0])
            else:
                for path in group_items:
                    error_corrected_version_is_present = (
                        "KonsolidierteLesefassungmitFehlerkorrekturen" in path.name
                        or "AußerordentlicheVeröffentlichung" in path.name
                    )
                    if error_corrected_version_is_present:
                        result.append(path)

        self.paths_to_docx_files = result

    def filter_docx_files_for_edifact_format(self, edifact_format: EdifactFormat) -> None:
        """
        Returns a list of docx files which contain the given edifact format.
        """

        self.paths_to_docx_files = [path for path in self.paths_to_docx_files if str(edifact_format) in path.name]

    def get_docx_files_which_may_contain_searched_pruefi(self, searched_pruefi: str) -> list[Path]:
        """
        This functions takes a pruefidentifikator and returns a list of docx files which can contain the searched pruefi
        Unfortunately, it is not clear in which docx the pruefidentifikator you are looking for is located.
        A 11042 belongs to the UTILMD format. However, there are seven docx files that describe the UTILMD format.
        A further reduction of the number of files is not possible with the pruefidentifikator only.
        """

        edifact_format = get_format_of_pruefidentifikator(searched_pruefi)
        if edifact_format is None:
            logger.exception("❌ There is no known format for the prüfi '%s'.", searched_pruefi)
            raise ValueError(f"There is no known format for the prüfi '{searched_pruefi}'.")

        self.filter_for_latest_ahb_docx_files()
        self.filter_docx_files_for_edifact_format(edifact_format=edifact_format)

        return self.paths_to_docx_files
