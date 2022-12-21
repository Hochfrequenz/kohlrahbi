from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pytest  # type:ignore[import]
import pytz
from maus.edifact import EdifactFormatVersion, get_edifact_format_version

from kohlrahbi.helper.read_functions import _get_format_version_from_ahbfile_name, remove_duplicates_from_ahb_list


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

    @pytest.mark.parametrize(
        "filename, expected_result",
        [
            pytest.param(
                "COMDISAHB-informatorischeLesefassung1.0cKonsolidierteLesefassungmitFehlerkorrekturenStand06.07.2022_99991231_20221001.docx",
                EdifactFormatVersion.FV2210,
            ),
            pytest.param(
                "COMDISAHB-informatorischeLesefassung1.0c_99991231_20221001.docx", EdifactFormatVersion.FV2210
            ),
            pytest.param("REQOTEQUOTESORDERSORDRSPORDCHGAHB2.1_99991231_20230401.docx", EdifactFormatVersion.FV2304),
            pytest.param("foo", get_edifact_format_version(datetime.utcnow().astimezone(tz=pytz.UTC))),
            pytest.param("bar", get_edifact_format_version(datetime.utcnow().astimezone(tz=pytz.UTC))),
        ],
    )
    def test_get_format_version_from_filename(self, filename: str, expected_result: Optional[EdifactFormatVersion]):
        actual = _get_format_version_from_ahbfile_name(filename)
        assert actual == expected_result
