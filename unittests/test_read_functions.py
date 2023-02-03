from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pytest  # type:ignore[import]
import pytz
from maus.edifact import EdifactFormatVersion, get_edifact_format_version

from kohlrahbi.read_functions import _get_format_version_from_ahbfile_name


class TestReadFunctions:
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
