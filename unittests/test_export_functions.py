from typing import Any

import pytest  # type:ignore[import]

from ahbextractor.helper.export_functions import beautify_bedingungen


class TestExportFunctions:
    @pytest.mark.parametrize(
        "argument, expected_result",
        [
            pytest.param(17, 17),
            pytest.param("17", "17"),
            pytest.param(None, None),
            pytest.param(
                "[12] Wenn SG4\n DTM+471 (Ende zum\n nächstmöglichen\nTermin) nicht vorhanden\n\n    [13] Wenn SG4\n STS+E01++Z01 (Status\nder Antwort: Zustimmung\nmit Terminänderung)\nnicht vorhanden",
                "[12] Wenn SG4 DTM+471 (Ende zum nächstmöglichen Termin) nicht vorhanden\n[13] Wenn SG4 STS+E01++Z01 (Status der Antwort: Zustimmung mit Terminänderung) nicht vorhanden",
            ),
        ],
    )
    def test_beautify_bedingungen(self, argument: Any, expected_result: Any):
        actual = beautify_bedingungen(argument)
        assert actual == expected_result
