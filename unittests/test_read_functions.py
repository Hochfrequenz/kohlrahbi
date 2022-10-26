from pathlib import Path
from typing import List

import pytest  # type:ignore[import]

from ahbextractor.helper.read_functions import remove_duplicates_from_ahb_list


class TestReadFunctions:
    @pytest.mark.parametrize(
        "argument, expected_result",
        [
            pytest.param(["A", "B"], ["A", "B"]),
            pytest.param(
                [
                    "COMDISAHB-informatorischeLesefassung1.0c_99991231_20221001.docx",
                    "COMDISAHB-informatorischeLesefassung1.0cKonsolidierteLesefassungmitFehlerkorrekturenStand06.07.2022_99991231_20221001.docx",
                    "B",
                ],
                [
                    "COMDISAHB-informatorischeLesefassung1.0cKonsolidierteLesefassungmitFehlerkorrekturenStand06.07.2022_99991231_20221001.docx",
                    "B",
                ],
            ),
            pytest.param(
                [
                    "foo/COMDISAHB-informatorischeLesefassung1.0c_99991231_20221001.docx",
                    "foo/COMDISAHB-informatorischeLesefassung1.0cKonsolidierteLesefassungmitFehlerkorrekturenStand06.07.2022_99991231_20221001.docx",
                    "B",
                ],
                [
                    "foo/COMDISAHB-informatorischeLesefassung1.0cKonsolidierteLesefassungmitFehlerkorrekturenStand06.07.2022_99991231_20221001.docx",
                    "B",
                ],
            ),
        ],
    )
    def test_remove_duplicate_from_ahb_list(self, argument: List[str], expected_result: List[str]):
        path_list = [Path(x) for x in argument]
        path_list_expected = [Path(x) for x in expected_result]
        remove_duplicates_from_ahb_list(path_list)
        assert path_list == path_list_expected
