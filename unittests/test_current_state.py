"""
This test will check if we get the same results during the refactoring process.
"""

import logging
from pathlib import Path
from typing import Union

import pytest
from click.testing import CliRunner, Result

from kohlrahbi import cli
from unittests import path_to_test_edi_energy_mirror_repo, path_to_test_files_fv2310

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


runner: CliRunner = CliRunner()


def get_csv_paths(root_dir) -> list[Path]:
    """Walk through root_dir and return paths of all CSV files."""
    root_path = Path(root_dir)
    return [path for path in root_path.rglob("*.csv")]


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
                    "--format-version",
                    "FV2310",
                    "--file-type",
                    "csv",
                ],
                {"exit_code": 0, "output_snippet": ""},
                id="proof of concept",
            )
        ],
    )
    def test_kohlrahbi_cli_with_valid_arguments(
        self, argument_options: list[str], expected_response: dict[str, Union[str, int]], snapshot
    ):
        """
        This test runs the CLI tool with valid arguments and checks if the output is as expected.
        """

        actual_output_dir = path_to_test_files_fv2310 / "actual-output"

        argument_options.extend(
            [
                "--edi-energy-mirror-path",
                str(path_to_test_edi_energy_mirror_repo),
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

        path_to_actual_csv_files = get_csv_paths(actual_output_dir)

        actual_csv_dict: dict[str, str] = {}
        for file in path_to_actual_csv_files:
            with open(file, "r", encoding="utf-8") as actual_csv:
                actual_csv_dict[file.name] = actual_csv.read()
        assert snapshot == actual_csv_dict
