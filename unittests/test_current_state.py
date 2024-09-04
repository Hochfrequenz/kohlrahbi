"""
This test will check if we get the same results during the refactoring process.
"""

import logging
from pathlib import Path
from typing import Union

import pytest
from click.testing import CliRunner, Result

from kohlrahbi import cli

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
                    "--assume-yes",
                    "--format-version",
                    "FV2404",
                    "--file-type",
                    "csv",
                    "-p",
                    "13002",
                    "-p",
                    "13014",
                    "-p",
                    "13023",
                    "-p",
                    "15002",
                    "-p",
                    "17002",
                    "-p",
                    "17010",
                    "-p",
                    "17114",
                    "-p",
                    "17129",
                    "-p",
                    "17201",
                    "-p",
                    "17208",
                    "-p",
                    "17301",
                    "-p",
                    "19002",
                    "-p",
                    "19007",
                    "-p",
                    "19016",
                    "-p",
                    "19103",
                    "-p",
                    "19120",
                    "-p",
                    "19131",
                    "-p",
                    "19204",
                    "-p",
                    "19301",
                    "-p",
                    "19302",
                    "-p",
                    "21002",
                    "-p",
                    "21010",
                    "-p",
                    "21015",
                    "-p",
                    "21030",
                    "-p",
                    "21039",
                    "-p",
                    "23001",
                    "-p",
                    "23009",
                    "-p",
                    "25001",
                    "-p",
                    "25003",
                    "-p",
                    "2504",
                    "-p",
                    "25006",
                    "-p",
                    "25009",
                    "-p",
                    "27001",
                    "-p",
                    "27003",
                    "-p",
                    "29001",
                    "-p",
                    "29002",
                    "-p",
                    "31001",
                    "-p",
                    "31003",
                    "-p",
                    "31007",
                    "-p",
                    "31011",
                    "-p",
                    "33004",
                    "-p",
                    "35001",
                    "-p",
                    "35004",
                    "-p",
                    "37000",
                    "-p",
                    "37002",
                    "-p",
                    "37005",
                    "-p",
                    "39000",
                    "-p",
                    "39002",
                    "-p",
                    "44001",
                    "-p",
                    "44005",
                    "-p",
                    "44009",
                    "-p",
                    "44016",
                    "-p",
                    "44023",
                    "-p",
                    "44040",
                    "-p",
                    "44053",
                    "-p",
                    "44103",
                    "-p",
                    "44105",
                    "-p",
                    "44112",
                    "-p",
                    "44117",
                    "-p",
                    "4413",
                    "-p",
                    "44140",
                    "-p",
                    "44148",
                    "-p",
                    "44163",
                    "-p",
                    "44180",
                    "-p",
                    "55003",
                    "-p",
                    "55009",
                    "-p",
                    "55014",
                    "-p",
                    "55035",
                    "-p",
                    "55041",
                    "-p",
                    "55062",
                    "-p",
                    "55074",
                    "-p",
                    "55075",
                    "-p",
                    "55077",
                    "-p",
                    "55081",
                    "-p",
                    "55086",
                    "-p",
                    "55093",
                    "-p",
                    "55105",
                    "-p",
                    "55115",
                    "-p",
                    "55127",
                    "-p",
                    "55147",
                    "-p",
                    "55157",
                    "-p",
                    "55182",
                    "-p",
                    "55200",
                    "-p",
                    "55213",
                    "-p",
                    "55555",
                ],
                {"exit_code": 0, "output_snippet": ""},
                id="proof of concept",
            )
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
                str(Path(__file__).parents[1] / "edi_energy_mirror"),  # path_to_test_edi_energy_mirror_repo),
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
