from pathlib import Path

import pytest
from efoli import EdifactFormatVersion

from kohlrahbi.docxfilefinder import DocxFileFinder, get_most_recent_file, split_version_string


class TestDocxFileFinder:
    @pytest.mark.parametrize(
        ["group_items", "expected"],
        [
            pytest.param(
                {"UTILTSAHB": [Path("AHB_UTILTS_4.0_20240701_20240701_20240401_xoxx_1001.docx")]},
                [Path("AHB_UTILTS_4.0_20240701_20240701_20240401_xoxx_1001.docx")],
                id="Single File",
            ),
            pytest.param(
                {
                    "UTILTSAHB": [
                        Path("AHB_UTILTS_4.0_20240701_20240701_20240401_xoxx_1002.docx"),
                        Path("AHB_UTILTS_4.0_20240701_20240701_20240501_oxox_1003.docx"),
                        Path("AHB_UTILTS_4.0_20240701_20240930_20240401_oxox_1004.docx"),
                        Path("AHB_UTILTS_4.0_20240701_20240930_20240701_xoxx_1005.docx"),
                        Path("AHB_UTILTS_4.0_20240701_20240930_20240501_xoxx_1006.docx"),
                    ]
                },
                [Path("AHB_UTILTS_4.0_20240701_20240930_20240701_xoxx_1005.docx")],
                id="Standard Case",
            ),
            pytest.param(
                {
                    "UTILTSAHB": [
                        Path("AHB_UTILTS_4.0_20240701_20240701_20240401_xoxx_1002.docx"),
                        Path("AHB_UTILTS_4.0_20240701_20240731_20240701_oxox_1003.docx"),
                        Path("AHB_UTILTS_4.0_20240701_20240930_20240401_oxox_1004.docx"),
                        Path("AHB_UTILTS_4.0_20240701_20240930_20240701_xoxx_1005.docx"),
                        Path("AHB_UTILTS_4.0_20240701_20240930_20240501_xoxx_1006.docx"),
                    ]
                },
                [Path("AHB_UTILTS_4.0_20240701_20240930_20240701_xoxx_1005.docx")],
                id="Valid from tie",
            ),
            pytest.param(
                {
                    "UTILMDAHBMaBiS": [
                        Path("AHB_UTILMD_4.0_20231001_99991231_20231001_ooox_2001.docx"),
                        Path("AHB_UTILMD_4.1a_20240403_20250403_20240403_xoxx_2002.docx"),
                        Path("AHB_UTILMD_4.1a_20240403_20250403_20240403_ooox_2003.docx"),
                    ]
                },
                [Path("AHB_UTILMD_4.1a_20240403_20250403_20240403_xoxx_2002.docx")],
                id="different names",
            ),
        ],
    )
    def test_filter_latest_version(self, group_items, expected):
        assert DocxFileFinder.filter_latest_version(group_items) == expected

    @pytest.mark.parametrize(
        ["group_items", "expected"],
        [
            pytest.param(
                [
                    Path("AHB_CONTRL_2.4a_20250404_99991231_20250404_xoxx_3001.docx"),
                    Path("AHB_CONTRL_2.4_20250404_99991231_20250404_xoxx_3002.docx"),
                ],
                Path("AHB_CONTRL_2.4a_20250404_99991231_20250404_xoxx_3001.docx"),
                id="Two versions of the same file",
            ),
            pytest.param(
                [
                    Path("AHB_COMDIS_1.3_20250404_99991231_20250404_xoxx_4001.docx"),
                    Path("AHB_COMDIS_1.1_20231001_99991231_20231001_xoxx_4002.docx"),
                    Path("AHB_COMDIS_1.3a_20250404_99991231_20250404_xoxx_4003.docx"),
                    Path("AHB_COMDIS_1.3b_20250404_99991231_20250404_xoxx_4004.docx"),
                ],
                Path("AHB_COMDIS_1.3b_20250404_99991231_20250404_xoxx_4004.docx"),
                id="Four versions of the same file",
            ),
        ],
    )
    def test_get_most_recent(self, group_items: list[Path], expected: Path):
        assert get_most_recent_file(group_items) == expected

    def test_split_version_string(self):
        assert split_version_string("1.0f") == ("", 1, 0, "f")
        assert split_version_string("1.0") == ("", 1, 0, "")
        assert split_version_string("1.0a") == ("", 1, 0, "a")
        assert split_version_string("2.0b") == ("", 2, 0, "b")
        assert split_version_string("4.2c") == ("", 4, 2, "c")
        assert split_version_string("S2.2c") == ("S", 2, 2, "c")

    @pytest.mark.parametrize(
        ["format_version", "base_path", "should_raise"],
        [
            pytest.param(
                EdifactFormatVersion.FV2504,
                Path("edi_energy_mirror/edi_energy_de"),
                False,
                id="Valid format version path",
            ),
            pytest.param(
                EdifactFormatVersion.FV2504,
                Path("non_existent_directory"),
                True,
                id="Valid format version but non-existent directory",
            ),
        ],
    )
    def test_get_validated_format_version_path(
        self, format_version, base_path, should_raise
    ):  # pylint: disable=protected-access
        docx_file_finder = DocxFileFinder(path_to_edi_energy_mirror=base_path)
        expected_path = base_path / format_version.value

        if should_raise:
            with pytest.raises(ValueError, match=f"Format version directory does not exist: {expected_path}"):
                docx_file_finder._get_validated_format_version_path(format_version)
        else:
            result = docx_file_finder._get_validated_format_version_path(format_version)
            assert result == expected_path

    # pylint: disable=protected-access
    def test_get_valid_docx_files(self, tmp_path):
        # Create test files
        valid_file1 = tmp_path / "test1.docx"
        valid_file2 = tmp_path / "test2.docx"
        temp_file = tmp_path / "~$temp.docx"  # Word temporary file
        non_docx_file = tmp_path / "test.txt"

        # Create the files
        valid_file1.touch()
        valid_file2.touch()
        temp_file.touch()
        non_docx_file.touch()

        docx_file_finder = DocxFileFinder(path_to_edi_energy_mirror=Path("dummy"))
        result = docx_file_finder._get_valid_docx_files(tmp_path)

        # Should include .docx files but exclude temporary files
        assert len(result) == 2
        assert valid_file1 in result
        assert valid_file2 in result
        assert temp_file not in result
        assert non_docx_file not in result

    def test_get_file_paths_for_change_history(self):
        path_to_edi_energy_mirror = Path("edi_energy_mirror") / Path("edi_energy_de")
        docx_file_finder = DocxFileFinder(path_to_edi_energy_mirror=path_to_edi_energy_mirror)

        paths_to_docx_files = docx_file_finder.get_file_paths_for_change_history(
            format_version=EdifactFormatVersion.FV2504
        )

        expected_paths = [
            path_to_edi_energy_mirror / "FV2504/AHB_COMDIS_1.0f_20250606_20250930_20250606_ooox_8871.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_CONTRL_2.4a_20250606_20250930_20250331_xoxx_11558.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_IFTSTA_2.0g_20250606_20250930_20250225_xoxx_11519.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_INSRPT_1.1g_20230330_99991231_20251211_oxox_12008.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_MSCONS_3.1f_20250930_20260331_20250930_xoxx_11889.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_ORDCHG_1.0a_20250606_20260930_20250606_ooox_11100.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_ORDERS_1.0a_20250623_20250930_20250623_xoxx_11750.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_ORDRSP_1.0a_20250606_20250930_20250606_ooox_11104.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_PARTIN_1.0e_20250606_20260331_20250606_ooox_9819.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_PRICAT_2.0e_20250623_20250930_20250623_xoxx_11756.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_QUOTES_1.0_20250606_20250930_20241213_xoxx_11146.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_REMADV_2.5d_20250623_20250930_20250623_xoxx_11767.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_REQOTE_1.0a_20250606_20250930_20250606_ooox_11109.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_UTILMD_G1.0a_20250930_20260331_20250930_xoxx_11901.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_UTILMD_S2.1_20250930_20251023_20250930_xoxx_11904.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_UTILTS_1.0_20250606_20250217_20250218_xoxx_11506.docx",
            path_to_edi_energy_mirror / "FV2504/EBD_4.0b_20250623_20250930_20250623_xoxx_11739.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_APERAK_2.1i_20250606_20260930_20250606_ooox_8671.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_COMDIS_1.0e_20250606_20250930_20250606_ooox_8885.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_CONTRL_2.0b_20221001_99991231_20251211_oxox_12006.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_IFTSTA_2.0f_20250606_20250930_20250225_xoxx_11522.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_INSRPT_1.1a_20230330_99991231_20240726_oxox_9355.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_INVOIC_2.8d_20250606_20250930_20250131_xoxx_11438.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_MSCONS_2.4c_20240403_20260930_20240726_oxox_9650.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_ORDCHG_1.1_20231001_20260930_20240726_oxox_9701.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_ORDERS_1.4a_20250606_20250930_20250218_xoxx_11509.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_ORDRSP_1.4_20250606_20250930_20250606_ooox_9797.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_PARTIN_1.0e_20250606_20260331_20250606_ooox_9836.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_PRICAT_2.0d_20250606_20250930_20250606_ooox_9982.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_QUOTES_1.3a_20250606_20251001_20241213_xoxx_11155.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_REMADV_2.9c_20240403_20250930_20240726_oxox_10040.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_REQOTE_1.3b_20250606_20250930_20250606_ooox_10067.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_UTILMD_G1.0a_20231212_20260331_20240726_oxox_10264.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_UTILMD_S2.1_20250606_20251210_20250319_xoxx_11549.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_UTILTS_1.1e_20250606_99991231_20241213_xoxx_11171.docx",
            path_to_edi_energy_mirror / "FV2504/allgemeinefestlegungen_6.1b_20250930_20260331_20250930_xoxx_11907.docx",
            path_to_edi_energy_mirror / "FV2504/apiguideline_1.0a_20250606_20260930_20250606_ooox_10824.docx",
            path_to_edi_energy_mirror
            / "FV2504/codelistederartikelnummernundartikelid_5.6_20250930_99991231_20250930_xoxx_11909.docx",
            path_to_edi_energy_mirror
            / "FV2504/codelistederkonfigurationen_1.3b_20250606_20250930_20250417_xoxx_11690.docx",
            path_to_edi_energy_mirror
            / "FV2504/codelistederlokationsbndelstrukturen_1.0_20241213_99991231_20241213_xoxx_11126.docx",
            path_to_edi_energy_mirror
            / "FV2504/codelistederobiskennzahlenundmedien_2.5b_20250930_20260331_20250930_xoxx_11911.docx",
            path_to_edi_energy_mirror
            / "FV2504/codelistedertemperaturanbieter_1.0i_20220726_99991231_20220726_ooox_8737.docx",
        ]

        # Convert paths to sets for comparison (order doesn't matter)
        actual_paths_set = set(paths_to_docx_files)
        expected_paths_set = set(expected_paths)

        # Check if the sets are equal
        assert actual_paths_set == expected_paths_set, (
            f"Mismatch in paths.\n"
            f"Missing paths (in expected but not in actual): {expected_paths_set - actual_paths_set}\n"
            f"Extra paths (in actual but not in expected): {actual_paths_set - expected_paths_set}"
        )

        # Also verify the count matches
        assert len(paths_to_docx_files) == len(expected_paths), (
            f"Number of paths doesn't match. "
            f"Expected {len(expected_paths)} paths, but got {len(paths_to_docx_files)}"
        )
