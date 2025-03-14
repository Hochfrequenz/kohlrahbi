"""
This test will check if we get the same results during the refactoring process.
"""

import logging
from pathlib import Path
from typing import Union

import pytest
from click.testing import CliRunner, Result

from kohlrahbi import cli
from unittests import current_state_pruefis

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


runner: CliRunner = CliRunner()


def get_csv_paths(root_dir) -> list[Path]:
    """Walk through root_dir and return paths of all CSV files."""
    root_path = Path(root_dir)
    return [path for path in root_path.rglob("*.csv")]


@pytest.mark.snapshot
class TestCli:
    """
    This class contains the unit tests for the CLI tool.
    """

    @pytest.mark.parametrize(
        "argument_options, expected_response",
        [
            pytest.param(
                [
                    "ahb",
                    "--assume-yes",
                    "--format-version",
                    "FV2404",
                    "--file-type",
                    "csv",
                    "-p",
                    pruefi,
                ],
                {"exit_code": 0, "output_snippet": ""},
                id=pruefi,
            )
            for pruefi in current_state_pruefis
        ],
    )
    def test_kohlrahbi_cli_with_valid_arguments(
        self, argument_options: list[str], expected_response: dict[str, Union[str, int]], snapshot, tmp_path
    ):
        """
        This test runs the CLI tool with valid arguments and checks if the output is as expected.
        """
        actual_output_dir = tmp_path / "actual-output"

        argument_options.extend(
            [
                "--edi-energy-mirror-path",
                str(Path(__file__).parents[1] / "edi_energy_mirror"),
                "--output-path",
                str(actual_output_dir),
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
