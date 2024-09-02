from pathlib import Path

import pytest

from kohlrahbi.docxfilefinder import DocxFileFinder


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
