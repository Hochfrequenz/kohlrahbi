from pathlib import Path
from typing import Union
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner, Result

from kohlrahbi import cli
from kohlrahbi.qualitymap import is_quality_map_table

runner: CliRunner = CliRunner()


class MockCell:
    def __init__(self, text):
        self.text = text

    def strip(self):
        return self.text.strip()


class MockTable:
    def __init__(self, cell_text):
        self.cell_text = cell_text

    def cell(self, row_idx, col_idx):
        if row_idx == 0 and col_idx == 0:
            return MockCell(self.cell_text)
        raise IndexError


@pytest.mark.snapshot
class TestQualityMap:

    def test_is_quality_map_table_true(self):
        table = MockTable("Qualität\n\nSegmentgruppe")
        assert is_quality_map_table(table) is True

    def test_is_quality_map_table_false(self):
        table = MockTable("Some other text")
        assert is_quality_map_table(table) is False

    def test_is_quality_map_table_index_error(self):
        table = MockTable(None)
        table.cell = MagicMock(side_effect=IndexError)
        assert is_quality_map_table(table) is False

    @pytest.mark.parametrize(
        "argument_options, expected_response",
        [
            pytest.param(
                [
                    "qualitymap",
                    "--format-version",
                    "FV2504",
                ],
                {"exit_code": 0, "output_snippet": ""},
                id="check",
            )
        ],
    )
    def test_cli_quality_map_table(
        self, argument_options: list[str], expected_response: dict[str, Union[str, int]], snapshot, tmp_path
    ):

        actual_output_dir = tmp_path / "actual-output"

        argument_options.extend(
            [
                "--edi-energy-mirror-path",
                str(Path(__file__).parents[1] / "edi_energy_mirror"),
                "--output-path",
                str(actual_output_dir),
                "--assume-yes",
            ]
        )

        # Call the CLI tool with the desired arguments
        response: Result = runner.invoke(cli, argument_options)

        assert response.exit_code == expected_response.get("exit_code")
        expected_output_snippet = expected_response.get("output_snippet")
        if expected_output_snippet is not None and isinstance(expected_output_snippet, str):
            assert expected_output_snippet in response.output
        else:
            assert False  # break the test if the output_snippet is None

        # Check if the generated files are the same as the expected files

        path_to_actual_csv_file = get_csv_paths(actual_output_dir)

        with open(path_to_actual_csv_file[0], "r", encoding="utf-8") as actual_csv:
            assert snapshot == actual_csv.read()
