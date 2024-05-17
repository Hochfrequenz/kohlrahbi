import pytest
from maus.edifact import EdifactFormat

from kohlrahbi.conditions import find_all_files_from_all_pruefis


class TestFindAllFiles:
    @pytest.mark.parametrize(
        "pruefi_to_file_mapping, expected_result",
        [
            pytest.param(
                {"11001": "file1.txt"},
                {EdifactFormat.UTILMD: ["file1.txt"]},
                id="single pruefi with a file",
            ),
            pytest.param(
                {"11001": "file1.txt", "11002": "file2.txt"},
                {EdifactFormat.UTILMD: ["file1.txt", "file2.txt"]},
                id="Multiple pruefis with files of the same format",
            ),
            pytest.param(
                {"11001": "file1.txt", "17206": "file2.txt", "21036": "file3.txt"},
                {
                    EdifactFormat.UTILMD: ["file1.txt"],
                    EdifactFormat.ORDERS: ["file2.txt"],
                    EdifactFormat.IFTSTA: ["file3.txt"],
                },
                id="Multiple pruefis with files of different formats",
            ),
        ],
    )
    def test_find_all_files(self, pruefi_to_file_mapping, expected_result):
        assert find_all_files_from_all_pruefis(pruefi_to_file_mapping) == expected_result

    def test_find_all_files_no_file(self):
        # No files provided
        pruefi_to_file_mapping = {"11001": None}
        with pytest.raises(ValueError, match="No file provided for pruefi 11001"):
            find_all_files_from_all_pruefis(pruefi_to_file_mapping)
