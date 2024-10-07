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


@pytest.fixture(scope="class")
def shared_tmp_path(tmp_path_factory):
    return tmp_path_factory.mktemp("shared")


def read_json_if_exists(file_path: Path):
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    return None


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


@pytest.mark.snapshot
class TestCliConditions:
    """
    Test the CLI tool conditions.
    """

    @freeze_time("2024-03-30")
    @pytest.mark.parametrize(
        "edifact_format",
        [
            pytest.param(
                edifact_format,
                id=edifact_format,
            )
            for edifact_format in edifact_formats
        ],
    )
    def test_cli_conditions(self, edifact_format, shared_tmp_path, snapshot) -> None:

        # run CLI command only for the first time
        if not any(shared_tmp_path.iterdir()):
            edi_repo_path = Path(str(Path(__file__).parents[1] / "edi_energy_mirror"))
            FV = "FV2404"

            argument_options: list[str] = [
                "--edi-energy-mirror-path",
                str(edi_repo_path),
                "--output-path",
                str(shared_tmp_path),
                "--format-version",
                FV,
            ]

            # Call the CLI tool with the desired arguments
            response: Result = runner.invoke(conditions, argument_options)

            assert response.exit_code == 0, "failed to run CLI conditions command"
        conditions_path = shared_tmp_path / str(edifact_format) / "conditions.json"
        packages_path = shared_tmp_path / str(edifact_format) / "packages.json"
        # assert that all files which should be generated do really exist
        assert conditions_path.exists(), "No matching file found for conditions"
        assert packages_path.exists() == snapshot  # not every format has packages
        # compare the generated files with the expected files
        assert snapshot == read_json_if_exists(conditions_path)
        assert snapshot == read_json_if_exists(packages_path)
