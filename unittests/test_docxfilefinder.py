from pathlib import Path, PosixPath

import pytest

from kohlrahbi.docxfilefinder import DocxFileFinder, get_most_recent_file


class TestDocxFileFinder:
    @pytest.mark.parametrize(
        ["group_items", "expected"],
        [
            pytest.param(
                {
                    "UTILTSAHB": [
                        Path("UTILTSAHB_20240701_20240401.docx"),
                    ]
                },
                [Path("UTILTSAHB_20240701_20240401.docx")],
                id="Single File",
            ),
            pytest.param(
                {
                    "UTILTSAHB": [
                        Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240701_20240401.docx"),
                        Path("UTILTSAHB-außerordentlicheveröffentlichung_20240701_20240501.docx"),
                        Path("UTILTSAHB-außerordentlicheveröffentlichung_20240930_20240401.docx"),
                        Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240701.docx"),
                        Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240501.docx"),
                    ]
                },
                [Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240701.docx")],
                id="Standard Case",
            ),
            pytest.param(
                {
                    "UTILTSAHB": [
                        Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240701_20240401.docx"),
                        Path("UTILTSAHB-außerordentlicheveröffentlichung_20240731_20240701.docx"),
                        Path("UTILTSAHB-außerordentlicheveröffentlichung_20240930_20240401.docx"),
                        Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240701.docx"),
                        Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240501.docx"),
                    ]
                },
                [Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240701.docx")],
                id="Valid from tie",
            ),
            pytest.param(
                {
                    "UTILTSAHB": [
                        Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240701_20240401.docx"),
                        Path("UTILTSAHB_20250731_20240901.docx"),
                        Path("UTILTSAHB-außerordentlicheveröffentlichung_20240930_20240401.docx"),
                        Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240701.docx"),
                        Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240501.docx"),
                    ]
                },
                [Path("UTILTSAHB-konsolidiertelesefassungmitfehlerkorrekturen_20240930_20240701.docx")],
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
                    PosixPath("APERAKCONTRLAHB-informatorischeLesefassung2.4a_99991231_20250404.docx"),
                    PosixPath("APERAKCONTRLAHB-informatorischeLesefassung2.4_99991231_20250404.docx"),
                ],
                Path("APERAKCONTRLAHB-informatorischeLesefassung2.4a_99991231_20250404.docx"),
                id="Two versions of the same file",
            ),
            pytest.param(
                [
                    PosixPath("CodelistederKonfigurationen-informatorischeLesefassung1.3_99991231_20250404.docx"),
                    PosixPath("CodelistederKonfigurationen-informatorischeLesefassung1.1_99991231_20231001.docx"),
                    PosixPath("CodelistederKonfigurationen-informatorischeLesefassung1.3a_99991231_20250404.docx"),
                    PosixPath("CodelistederKonfigurationen-informatorischeLesefassung1.3b_99991231_20250404.docx"),
                ],
                Path("CodelistederKonfigurationen-informatorischeLesefassung1.3b_99991231_20250404.docx"),
                id="Four versions of the same file",
            ),
        ],
    )
    def test_get_most_recent(self, group_items: list[Path], expected: Path):
        assert get_most_recent_file(group_items) == expected
