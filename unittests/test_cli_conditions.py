"""
This module contains the tests for the CLI tool conditions.
"""

import json
import os
from pathlib import Path

from click.testing import CliRunner, Result
from efoli import EdifactFormat
from freezegun import freeze_time

from kohlrahbi.conditions.command import conditions
from unittests import path_to_test_edi_energy_mirror_repo, path_to_test_files_fv2310

runner: CliRunner = CliRunner()


class TestCliConditions:
    """
    Test the CLI tool conditions.
    """

    @freeze_time("2024-03-30")
    def test_cli_conditions(self) -> None:
        """
        This test runs the CLI tool with valid arguments and checks if the output is as expected.
        """

        actual_output_dir = path_to_test_files_fv2310 / "actual-output"
        expected_output_dir = path_to_test_files_fv2310 / "expected-output"

        argument_options: list[str] = [
            "--edi-energy-mirror-path",
            str(path_to_test_edi_energy_mirror_repo),
            "--output-path",
            str(actual_output_dir),
            "--format-version",
            "FV2310",
        ]

        # Call the CLI tool with the desired arguments
        response: Result = runner.invoke(conditions, argument_options)

        assert response.exit_code == 0

        # collect all test formats
        edifact_formats = []
        for item in os.listdir(expected_output_dir):
            item_path = os.path.join(expected_output_dir, item)
            if os.path.isdir(item_path):
                edifact_formats.append(EdifactFormat(item))

        for edifact_format in edifact_formats:
            # asssert that all files which should be generated do really exist
            assert (actual_output_dir / str(edifact_format) / "conditions.json").exists(), "No matching file found"
            assert (expected_output_dir / str(edifact_format) / "packages.json").exists() == (
                actual_output_dir / str(edifact_format) / "packages.json"
            ).exists()
            # compare the generated files with the expected files
            with open(
                expected_output_dir / Path(str(edifact_format)) / Path("conditions.json"), "r", encoding="utf-8"
            ) as file:
                expected_cond_dict = json.load(file)
            with open(
                actual_output_dir / Path(str(edifact_format)) / Path("conditions.json"), "r", encoding="utf-8"
            ) as file:
                actual_cond_dict = json.load(file)
            assert actual_cond_dict == expected_cond_dict
            if Path(actual_output_dir, Path(str(edifact_format)) / Path("packages.json")).exists():
                with open(
                    expected_output_dir / Path(str(edifact_format)) / Path("packages.json"), "r", encoding="utf-8"
                ) as file:
                    expected_package_dict = json.load(file)
                with open(
                    actual_output_dir / Path(str(edifact_format)) / Path("packages.json"), "r", encoding="utf-8"
                ) as file:
                    actual_package_dict = json.load(file)

                assert actual_package_dict == expected_package_dict
