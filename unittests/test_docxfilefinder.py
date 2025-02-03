from pathlib import Path, PosixPath

import pytest

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
        assert split_version_string("1.0f") == (1, 0, "f")
        assert split_version_string("1.0") == (1, 0, "")
        assert split_version_string("1.0a") == (1, 0, "a")
        assert split_version_string("2.0b") == (2, 0, "b")
        assert split_version_string("4.2c") == (4, 2, "c")
