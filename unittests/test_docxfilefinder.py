from pathlib import Path

import pytest
from efoli import EdifactFormatVersion

from kohlrahbi.docxfilefinder import DocxFileFinder, get_most_recent_file, split_version_string


class TestDocxFileFinder:
    @pytest.mark.parametrize(
        ["group_items", "expected"],
        [
            pytest.param(
                {"UTILTSAHB": [Path("UTILTSAHB-informatorischeLesefassung4.0_20240701_20240401.docx")]},
                [Path("UTILTSAHB-informatorischeLesefassung4.0_20240701_20240401.docx")],
                id="Single File",
            ),
            pytest.param(
                {
                    "UTILTSAHB": [
                        Path(
                            "UTILTSAHB-informatorischeLesefassung4.0Konsolidiertelesefassungmitfehlerkorrekturen_20240701_20240401.docx"
                        ),
                        Path(
                            "UTILTSAHB-informatorischeLesefassung4.0-außerordentlicheveröffentlichung_20240701_20240501.docx"
                        ),
                        Path(
                            "UTILTSAHB-informatorischeLesefassung4.0-außerordentlicheveröffentlichung_20240930_20240401.docx"
                        ),
                        Path(
                            "UTILTSAHB-informatorischeLesefassung4.0Konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240701.docx"
                        ),
                        Path(
                            "UTILTSAHB-informatorischeLesefassung4.0Konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240501.docx"
                        ),
                    ]
                },
                [
                    Path(
                        "UTILTSAHB-informatorischeLesefassung4.0Konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240701.docx"
                    )
                ],
                id="Standard Case",
            ),
            pytest.param(
                {
                    "UTILTSAHB": [
                        Path(
                            "UTILTSAHB-informatorischeLesefassung4.0Konsolidiertelesefassungmitfehlerkorrekturen_20240701_20240401.docx"
                        ),
                        Path(
                            "UTILTSAHB-informatorischeLesefassung4.0-außerordentlicheveröffentlichung_20240731_20240701.docx"
                        ),
                        Path(
                            "UTILTSAHB-informatorischeLesefassung4.0-außerordentlicheveröffentlichung_20240930_20240401.docx"
                        ),
                        Path(
                            "UTILTSAHB-informatorischeLesefassung4.0Konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240701.docx"
                        ),
                        Path(
                            "UTILTSAHB-informatorischeLesefassung4.0Konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240501.docx"
                        ),
                    ]
                },
                [
                    Path(
                        "UTILTSAHB-informatorischeLesefassung4.0Konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240701.docx"
                    )
                ],
                id="Valid from tie",
            ),
            pytest.param(
                {
                    "UTILMDAHBMaBiS": [
                        Path("UTILMDAHBMaBiS-informatorischeLesefassung4.0_99991231_20231001.docx"),
                        Path(
                            "UTILMDAHBMaBiS-informatorischeLesefassung4.1aKonsolidierteLesefassungmitFehlerkorrekturenStand11.03.2024_20250403_20240403.docx"
                        ),
                        Path("UTILMDAHBMaBiS-informatorischeLesefassung4.1a_20250403_20240403.docx"),
                    ]
                },
                [
                    Path(
                        "UTILMDAHBMaBiS-informatorischeLesefassung4.1aKonsolidierteLesefassungmitFehlerkorrekturenStand11.03.2024_20250403_20240403.docx"
                    )
                ],
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
                    Path("APERAKCONTRLAHB-informatorischeLesefassung2.4a_99991231_20250404.docx"),
                    Path("APERAKCONTRLAHB-informatorischeLesefassung2.4_99991231_20250404.docx"),
                ],
                Path("APERAKCONTRLAHB-informatorischeLesefassung2.4a_99991231_20250404.docx"),
                id="Two versions of the same file",
            ),
            pytest.param(
                [
                    Path("CodelistederKonfigurationen-informatorischeLesefassung1.3_99991231_20250404.docx"),
                    Path("CodelistederKonfigurationen-informatorischeLesefassung1.1_99991231_20231001.docx"),
                    Path("CodelistederKonfigurationen-informatorischeLesefassung1.3a_99991231_20250404.docx"),
                    Path("CodelistederKonfigurationen-informatorischeLesefassung1.3b_99991231_20250404.docx"),
                ],
                Path("CodelistederKonfigurationen-informatorischeLesefassung1.3b_99991231_20250404.docx"),
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

    def test_get_file_paths_for_change_history(self):
        path_to_edi_energy_mirror = Path("edi_energy_mirror") / Path("edi_energy_de")
        docx_file_finder = DocxFileFinder(path_to_edi_energy_mirror=path_to_edi_energy_mirror)

        paths_to_docx_files = docx_file_finder.get_file_paths_for_change_history(
            format_version=EdifactFormatVersion.FV2504
        )

        expected_paths = [
            path_to_edi_energy_mirror / "FV2504/AHB_COMDIS_1.0f_20250606_99991231_20250606_oxox_11427.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_CONTRL_2.4a_20250606_99991231_20241213_xoxx_11128.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_IFTSTA_2.0g_20250606_99991231_20241213_xoxx_11132.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_MSCONS_3.1f_20250606_99991231_20250606_ooox_9612.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_ORDCHG_1.0a_20250606_99991231_20250606_ooox_11100.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_ORDERS_1.0a_20250606_99991231_20250131_xoxx_11441.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_ORDRSP_1.0a_20250606_99991231_20250606_ooox_11104.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_PARTIN_1.0e_20250606_99991231_20250606_ooox_9819.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_PRICAT_2.0e_20250606_99991231_20250606_ooox_9965.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_QUOTES_1.0_20250606_99991231_20241213_xoxx_11146.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_REMADV_2.5d_20250606_99991231_20250131_xoxx_11434.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_REQOTE_1.0a_20250606_99991231_20250606_ooox_11109.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_UTILMD_2.1_20250606_99991231_20241213_xoxx_11157.docx",
            path_to_edi_energy_mirror / "FV2504/AHB_UTILTS_1.0_20250606_99991231_20241213_xoxx_11164.docx",
            path_to_edi_energy_mirror / "FV2504/EBD_4.0b_20250606_99991231_20250131_xoxx_11425.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_APERAK_2.1i_20250606_99991231_20250606_ooox_8671.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_COMDIS_1.0e_20250606_99991231_20250606_ooox_8885.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_IFTSTA_2.0f_20250606_99991231_20250606_ooox_9326.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_INVOIC_2.8d_20250606_99991231_20250131_xoxx_11438.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_ORDERS_1.4a_20250606_99991231_20241213_xoxx_11139.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_ORDRSP_1.4_20250606_99991231_20250606_ooox_9797.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_PARTIN_1.0e_20250606_99991231_20250606_ooox_9836.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_PRICAT_2.0d_20250606_99991231_20250606_ooox_9982.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_QUOTES_1.3a_20250606_99991231_20241213_xoxx_11155.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_REQOTE_1.3b_20250606_99991231_20250606_ooox_10067.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_UTILMD_S2.1_20250606_99991231_20250131_xoxx_11449.docx",
            path_to_edi_energy_mirror / "FV2504/MIG_UTILTS_1.1e_20250606_99991231_20241213_xoxx_11171.docx",
            path_to_edi_energy_mirror
            / "FV2504/allgemeinefestlegungeninformatorischelesefassung_6.1b_20250606_99991231_20250606_ooox_8638.docx",
            path_to_edi_energy_mirror
            / "FV2504/apiguidelineinformatorischelesefassung_1.0a_20250606_99991231_20250606_ooox_10824.docx",
            path_to_edi_energy_mirror
            / "FV2504/codelistederkonfigurationen_1.3b_20250606_99991231_20241213_xoxx_11124.docx",
            path_to_edi_energy_mirror
            / "FV2504/codelistederkonfigurationeninformatorischelesefassung_1.3b_20250606_99991231_20250606_ooox_8757.docx",
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
