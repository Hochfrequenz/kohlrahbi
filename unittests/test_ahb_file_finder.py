from itertools import groupby
from pathlib import Path

import pytest  # type:ignore[import]
from maus.edifact import EdifactFormat

from kohlrahbi.ahbfilefinder import AhbFileFinder


class TestAhbFileFinder:
    """
    This class contains the unit tests for the AhbFileFinder class.
    """

    @pytest.mark.parametrize(
        "searched_pruefi, expected_docx_count",
        [
            pytest.param(
                "11042",
                6,
                id="11042 - Anmeldung MSB",
            ),
            pytest.param(
                "13002",
                1,
                id="13002 - Zaehlerstand (Gas)",
            ),
        ],
    )
    def test_get_docx_files_which_may_contain_searched_pruefi(self, searched_pruefi, expected_docx_count):
        path_to_ahb_documents: Path = Path.cwd() / Path("unittests/docx_files")

        ahb_file_finder = AhbFileFinder.from_input_path(input_path=path_to_ahb_documents)

        ahb_file_finder.get_docx_files_which_may_contain_searched_pruefi(searched_pruefi=searched_pruefi)

        assert len(ahb_file_finder.paths_to_docx_files) == expected_docx_count

    def test_filter_docx_files_for_edifact_format(self):
        """
        Test the filter_docx_files_for_edifact_format method.
        This method filters the list of AHB docx paths for the given EDIFACT format.
        But it does not filter for the latest AHB docx files.
        So we assert two ahb files for the MSCONS format:
        - MSCONSAHB-informatorischeLesefassung3.1a_20230331_20221001
        - MSCONSAHB-informatorischeLesefassung3.1aKonsolidierteLesefassungmitFehlerkorrekturenStand27.09.2022_20230331_20221001
        """
        path_to_ahb_documents: Path = Path.cwd() / Path("unittests/docx_files")

        ahb_file_finder = AhbFileFinder.from_input_path(input_path=path_to_ahb_documents)

        ahb_file_finder.filter_docx_files_for_edifact_format(edifact_format=EdifactFormat.MSCONS)

        assert len(ahb_file_finder.paths_to_docx_files) == 2

    def test_filter_for_latest_ahb_docx_files(self):
        """
        Test the filter_for_latest_ahb_docx_files method.
        This method filters the list of AHB docx paths for the latest AHB docx files.
        The latest files contain `LesefassungmitFehlerkorrekturen` in their file names.
        """
        path_to_ahb_documents: Path = Path.cwd() / Path("unittests/docx_files")

        ahb_file_finder = AhbFileFinder.from_input_path(input_path=path_to_ahb_documents)

        ahb_file_finder.filter_for_latest_ahb_docx_files()

        assert len(ahb_file_finder.paths_to_docx_files) == 18
