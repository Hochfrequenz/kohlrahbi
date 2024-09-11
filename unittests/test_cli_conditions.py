"""
This module contains the tests for the CLI tool conditions.
"""

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from efoli import EdifactFormat
from freezegun import freeze_time

from kohlrahbi.conditions.command import conditions
from unittests import path_to_test_files_fv2310

runner: CliRunner = CliRunner()


@pytest.mark.snapshot
class TestCliConditions:
    """
    Test the CLI tool conditions.
    """

    @freeze_time("2024-03-30")
    def test_cli_conditions(self, tmp_path, snapshot) -> None:
        """
        This test runs the CLI tool with valid arguments and checks if the output is as expected.
        """
        edi_repo_path = Path(str(Path(__file__).parents[1] / "edi_energy_mirror"))
        FV = "FV2404"

        argument_options: list[str] = [
            "--edi-energy-mirror-path",
            str(edi_repo_path),
            "--output-path",
            str(tmp_path),
            "--format-version",
            FV,
        ]

        # Call the CLI tool with the desired arguments
        response: Result = runner.invoke(conditions, argument_options)

        assert response.exit_code == 0

        # collect all test formats
        edifact_formats = [
            EdifactFormat.COMDIS,
            EdifactFormat.IFTSTA,
            EdifactFormat.INSRPT,
            EdifactFormat.INVOIC,
            EdifactFormat.MSCONS,
            EdifactFormat.ORDCHG,
            EdifactFormat.ORDERS,
            EdifactFormat.ORDRSP,
            EdifactFormat.PARTIN,
            EdifactFormat.PRICAT,
            EdifactFormat.QUOTES,
            EdifactFormat.REMADV,
            EdifactFormat.REQOTE,
            EdifactFormat.UTILMD,
            EdifactFormat.UTILTS,
        ]

        for edifact_format in sorted(edifact_formats):

            # asssert that all files which should be generated do really exist
            assert (
                tmp_path / str(edifact_format) / "conditions.json"
            ).exists(), "No matching file found for conditions"
            assert (tmp_path / str(edifact_format) / "packages.json").exists(), "No matching file found for packages"
            # compare the generated files with the expected files
            with open(tmp_path / Path(str(edifact_format)) / Path("conditions.json"), "r", encoding="utf-8") as file:
                assert snapshot == json.load(file)
            with open(tmp_path / Path(str(edifact_format)) / Path("packages.json"), "r", encoding="utf-8") as file:
                assert snapshot == json.load(file)
