from pathlib import Path

import pytest
from efoli import EdifactFormatVersion

from kohlrahbi.docxfilefinder import DocxFileFinder, split_version_string


class TestDocxFileFinder:
    def test_split_version_string(self):
        assert split_version_string("1.0f") == ("", 1, 0, "f")
        assert split_version_string("1.0") == ("", 1, 0, "")
        assert split_version_string("1.0a") == ("", 1, 0, "a")
        assert split_version_string("2.0b") == ("", 2, 0, "b")
        assert split_version_string("4.2c") == ("", 4, 2, "c")
        assert split_version_string("S2.2c") == ("S", 2, 2, "c")

    def test_get_valid_docx_files(self, tmp_path):
        """Test that _get_valid_docx_files correctly identifies and filters docx files."""
        # Create a mock format version directory structure
        format_version = EdifactFormatVersion.FV2504
        format_dir = tmp_path / "edi_energy_de" / format_version.value
        format_dir.mkdir(parents=True)

        # Create test files
        valid_files = [format_dir / "test1.docx", format_dir / "test2.docx", format_dir / "AHB_UTILMD_2.1.docx"]
        temp_files = [
            format_dir / "~$temp.docx",  # Word temporary file
            format_dir / "~WRL0001.tmp",  # Another temp file
        ]
        other_files = [format_dir / "test.txt", format_dir / "test.pdf", format_dir / "test.doc"]

        # Create all the test files
        for file in valid_files + temp_files + other_files:
            file.touch()

        # Initialize DocxFileFinder with the test directory
        docx_file_finder = DocxFileFinder(path_to_edi_energy_mirror=tmp_path, format_version=format_version)

        # Call the method
        docx_file_finder._get_valid_docx_files()  # pylint: disable=protected-access

        # Verify results
        assert len(docx_file_finder.result_paths) == len(valid_files)
        assert all(path in docx_file_finder.result_paths for path in valid_files)
        assert all(path not in docx_file_finder.result_paths for path in temp_files)
        assert all(path not in docx_file_finder.result_paths for path in other_files)

    def test_get_valid_docx_files_empty_directory(self, tmp_path):
        """Test that _get_valid_docx_files handles empty directories correctly."""
        # Create empty format version directory
        format_version = EdifactFormatVersion.FV2504
        format_dir = tmp_path / "edi_energy_de" / format_version.value
        format_dir.mkdir(parents=True)

        # Initialize DocxFileFinder with the empty directory
        docx_file_finder = DocxFileFinder(path_to_edi_energy_mirror=tmp_path, format_version=format_version)

        # Call the method
        docx_file_finder._get_valid_docx_files()  # pylint: disable=protected-access

        # Verify results
        assert len(docx_file_finder.result_paths) == 0
        assert isinstance(docx_file_finder.result_paths, list)

    @pytest.mark.parametrize(
        ["initial_paths", "expected_paths"],
        [
            pytest.param(
                [
                    Path("UTILMDAHBMaBiS-informatorischeLesefassung4.0.docx"),
                    Path("UTILMD-informatorischeLesefassung4.0.docx"),
                    Path("APERAKAHB-informatorischeLesefassung2.0.docx"),
                    Path("MIG-informatorischeLesefassung1.0.docx"),
                ],
                [
                    Path("UTILMDAHBMaBiS-informatorischeLesefassung4.0.docx"),
                    Path("APERAKAHB-informatorischeLesefassung2.0.docx"),
                ],
                id="mixed_files",
            ),
            pytest.param(
                [
                    Path("UTILMD-informatorischeLesefassung4.0.docx"),
                    Path("MIG-informatorischeLesefassung1.0.docx"),
                ],
                [],
                id="no_ahb_files",
            ),
            pytest.param(
                [
                    Path("UTILMDAHBMaBiS-informatorischeLesefassung4.0.docx"),
                    Path("APERAKAHB-informatorischeLesefassung2.0.docx"),
                ],
                [
                    Path("UTILMDAHBMaBiS-informatorischeLesefassung4.0.docx"),
                    Path("APERAKAHB-informatorischeLesefassung2.0.docx"),
                ],
                id="only_ahb_files",
            ),
        ],
    )
    def test_filter_for_ahb_docx_files(self, initial_paths, expected_paths):
        """Test that _filter_for_ahb_docx_files correctly filters for AHB files."""
        # Create DocxFileFinder instance with required format_version
        docx_file_finder = DocxFileFinder(
            path_to_edi_energy_mirror=Path("dummy"), format_version=EdifactFormatVersion.FV2504
        )
        # Set initial paths
        docx_file_finder.result_paths = initial_paths
        # Apply filter
        docx_file_finder._filter_for_ahb_docx_files()  # pylint: disable=protected-access
        # Verify results
        assert sorted(docx_file_finder.result_paths) == sorted(expected_paths)

    def test_filter_informational_versions(self):
        """Test that _filter_informational_versions correctly filters for informational reading versions."""
        # Create DocxFileFinder instance
        docx_file_finder = DocxFileFinder(
            path_to_edi_energy_mirror=Path("dummy"), format_version=EdifactFormatVersion.FV2504
        )

        # Set up test paths with mix of informational and non-informational versions
        docx_file_finder.result_paths = [
            # Informational reading versions
            Path("AHB_COMDIS_1.0f_20250606_99991231_20250606_ooox_8871.docx"),
            Path("AHB_CONTRL_2.4a_20250606_99991231_20241213_xoxx_11128.docx"),
            Path("MIG_UTILMD_S2.1_20250606_20250129_20241213_xoxx_11161.docx"),
            # Non-informational versions
            Path("AHB_COMDIS_1.0f_20250606_99991231_20250606_oooo_8872.pdf"),
            Path("AHB_CONTRL_2.4a_20250606_99991231_20250606_oooo_8927.pdf"),
            Path("MIG_UTILMD_S2.1_20250606_20250129_20241213_xoxo_11160.pdf"),
        ]

        # Expected results (only informational reading versions)
        expected_paths = [
            Path("AHB_COMDIS_1.0f_20250606_99991231_20250606_ooox_8871.docx"),
            Path("AHB_CONTRL_2.4a_20250606_99991231_20241213_xoxx_11128.docx"),
            Path("MIG_UTILMD_S2.1_20250606_20250129_20241213_xoxx_11161.docx"),
        ]

        # Apply filter
        docx_file_finder._filter_informational_versions()  # pylint: disable=protected-access

        # Verify results
        assert len(docx_file_finder.result_paths) == len(expected_paths)
        assert sorted(docx_file_finder.result_paths) == sorted(expected_paths)

    def test_filter_informational_versions_empty(self):
        """Test that _filter_informational_versions handles empty input correctly."""
        # Create DocxFileFinder instance
        docx_file_finder = DocxFileFinder(
            path_to_edi_energy_mirror=Path("dummy"), format_version=EdifactFormatVersion.FV2504
        )

        # Test with empty list
        docx_file_finder.result_paths = []
        docx_file_finder._filter_informational_versions()  # pylint: disable=protected-access
        assert len(docx_file_finder.result_paths) == 0

    def test_filter_informational_versions_no_informational(self):
        """Test that _filter_informational_versions handles case with no informational versions."""
        # Create DocxFileFinder instance
        docx_file_finder = DocxFileFinder(
            path_to_edi_energy_mirror=Path("dummy"), format_version=EdifactFormatVersion.FV2504
        )

        # Set up test paths with only non-informational versions
        docx_file_finder.result_paths = [
            Path("AHB_COMDIS_1.0f_20250606_99991231_20250606_oooo_8872.pdf"),
            Path("AHB_CONTRL_2.4a_20250606_99991231_20250606_oooo_8927.pdf"),
            Path("MIG_ORDRSP_1.4_20250606_99991231_20250606_oooo_9796.pdf"),
        ]

        # Apply filter
        docx_file_finder._filter_informational_versions()  # pylint: disable=protected-access

        # Verify results
        assert len(docx_file_finder.result_paths) == 0

    def test_get_most_recent_versions(self):
        """Test that _get_most_recent_versions correctly identifies the most recent version of each document."""
        # Create DocxFileFinder instance
        docx_file_finder = DocxFileFinder(
            path_to_edi_energy_mirror=Path("dummy"), format_version=EdifactFormatVersion.FV2504
        )

        # Set up test paths with multiple versions of documents
        docx_file_finder.result_paths = [
            # COMDIS versions
            Path("AHB_COMDIS_1.0f_20250606_99991231_20250606_ooox_8871.docx"),
            Path(
                "AHB_COMDIS_1.0f_20250606_99991231_20250606_oxox_11427.docx"
            ),  # most recent, extraordinary publication
            # CONTRL versions
            Path("AHB_CONTRL_2.4a_20250606_99991231_20250606_ooox_8928.docx"),
            # UTILMD versions
            Path("MIG_UTILMD_S2.1_20250606_20250129_20241213_xoxx_11161.docx"),
            Path("MIG_UTILMD_S2.1_20250606_99991231_20250131_xoxx_11449.docx"),
            Path("MIG_UTILMD_S2.1_20250606_99991231_20250606_ooox_10660.docx"),
            # MSCONS versions
            Path("AHB_MSCONS_3.1_20250606_99991231_20250606_ooox_9612.docx"),
        ]

        # Expected results (only most recent versions)
        expected_paths = [
            Path("AHB_COMDIS_1.0f_20250606_99991231_20250606_oxox_11427.docx"),
            Path("AHB_CONTRL_2.4a_20250606_99991231_20250606_ooox_8928.docx"),
            Path("MIG_UTILMD_S2.1_20250606_99991231_20250131_xoxx_11449.docx"),
            Path("AHB_MSCONS_3.1_20250606_99991231_20250606_ooox_9612.docx"),
        ]

        # Apply filter
        docx_file_finder._get_most_recent_versions()  # pylint: disable=protected-access

        # Verify results
        assert len(docx_file_finder.result_paths) == len(expected_paths)
        assert sorted(docx_file_finder.result_paths) == sorted(expected_paths)

    def test_get_most_recent_versions_empty(self):
        """Test that _get_most_recent_versions handles empty input correctly."""
        docx_file_finder = DocxFileFinder(
            path_to_edi_energy_mirror=Path("dummy"), format_version=EdifactFormatVersion.FV2504
        )
        docx_file_finder.result_paths = []
        docx_file_finder._get_most_recent_versions()  # pylint: disable=protected-access
        assert len(docx_file_finder.result_paths) == 0

    def test_get_most_recent_versions_single_files(self):
        """Test that _get_most_recent_versions correctly handles groups with single files."""
        docx_file_finder = DocxFileFinder(
            path_to_edi_energy_mirror=Path("dummy"), format_version=EdifactFormatVersion.FV2504
        )

        # Set up test paths with single files of different types
        input_paths = [
            Path("AHB_COMDIS_1.0f_20250606_99991231_20250606_ooox_8871.docx"),
            Path("AHB_CONTRL_2.4a_20250606_99991231_20241213_xoxx_11128.docx"),
            Path("MIG_UTILMD_S2.1_20250606_20250129_20241213_xoxx_11161.docx"),
        ]
        docx_file_finder.result_paths = input_paths.copy()

        # Apply filter
        docx_file_finder._get_most_recent_versions()  # pylint: disable=protected-access

        # Verify results - should be same as input since each file is unique
        assert len(docx_file_finder.result_paths) == len(input_paths)
        assert sorted(docx_file_finder.result_paths) == sorted(input_paths)

    def test_get_most_recent_versions_with_error_corrections(self):
        """Test that _get_most_recent_versions correctly prioritizes error correction versions."""
        docx_file_finder = DocxFileFinder(
            path_to_edi_energy_mirror=Path("dummy"), format_version=EdifactFormatVersion.FV2504
        )

        # Set up test paths with error corrections and regular versions
        docx_file_finder.result_paths = [
            # Regular versions
            Path("AHB_COMDIS_1.0f_20250606_99991231_20250606_oooo_8872.docx"),
            Path("AHB_CONTRL_2.4a_20250606_99991231_20250606_oooo_8927.docx"),
            Path("MIG_UTILMD_S2.1_20250606_20250129_20241213_xoxo_11160.docx"),
            # Error correction versions (should be preferred)
            Path("AHB_COMDIS_1.0f_20250606_99991231_20250606_ooox_8871.docx"),
            Path("AHB_CONTRL_2.4a_20250606_99991231_20241213_xoxx_11128.docx"),
            Path("MIG_UTILMD_S2.1_20250606_20250129_20241213_xoxx_11161.docx"),
        ]

        # Expected results (only error correction versions)
        expected_paths = [
            Path("AHB_COMDIS_1.0f_20250606_99991231_20250606_ooox_8871.docx"),
            Path("AHB_CONTRL_2.4a_20250606_99991231_20241213_xoxx_11128.docx"),
            Path("MIG_UTILMD_S2.1_20250606_20250129_20241213_xoxx_11161.docx"),
        ]

        # Apply filter
        docx_file_finder._get_most_recent_versions()  # pylint: disable=protected-access

        # Verify results
        assert len(docx_file_finder.result_paths) == len(expected_paths)
        assert sorted(docx_file_finder.result_paths) == sorted(expected_paths)
