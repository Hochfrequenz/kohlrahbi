from pathlib import Path
from typing import Union

import pytest
from typer.testing import CliRunner

from kohlrahbi import app
from unittests import path_to_test_edi_energy_mirror_repo, path_to_test_files_fv2310

runner = CliRunner()


class TestCliPruefi:
    """
    This class contains the unit tests for the CLI tool.
    """

    @pytest.mark.parametrize(
        "argument_options, expected_response",
        [
            pytest.param(
                [
                    "ahb",
                    "--pruefis",
                    "11016",
                    "--edi-energy-mirror-path",
                    "/invalid/input/path",
                    "--format-version",
                    "FV2310",
                    "--file-type",
                    "csv",
                ],
                {"exit_code": 2, "output_snippet": "invalid/input/path"},
                id="invalid input path",
            ),
            pytest.param(
                [
                    "ahb",
                    "--pruefis",
                    "11016",
                    "--edi-energy-mirror-path",
                    path_to_test_edi_energy_mirror_repo,
                    "--output-path",
                    "/invalid/output/path",
                    "--format-version",
                    "FV2310",
                    "--file-type",
                    "csv",
                ],
                {"exit_code": 1, "output_snippet": "invalid/output/path"},
                id="invalid output path",
            ),
            pytest.param(
                [
                    "ahb",
                    "--pruefis",
                    "abc",
                    "--edi-energy-mirror-path",
                    path_to_test_edi_energy_mirror_repo,
                    "--output-path",
                    path_to_test_files_fv2310,
                    "--format-version",
                    "FV2310",
                    "--file-type",
                    "csv",
                ],
                {"exit_code": 1, "output_snippet": "no valid pruefidentifika"},
                id="invalid pruefidentifikator",
            ),
        ],
    )
    def test_cli_pruefi_with_invalid_arguments(
        self, argument_options: list[str], expected_response: dict[str, Union[str, int]]
    ) -> None:
        """
        This test runs the CLI tool with invalid arguments and checks if the output is as expected.
        """

        # Call the CLI tool with the desired arguments
        response = runner.invoke(app, argument_options)

        assert response.exit_code == expected_response.get("exit_code")
        output_snippet = expected_response.get("output_snippet")
        assert isinstance(output_snippet, str)
        assert output_snippet.lower() in response.output.lower()

    @pytest.mark.parametrize(
        "argument_options, expected_response",
        [
            pytest.param(
                [
                    "ahb",
                    "-p",
                    "17201",
                    "--format-version",
                    "FV2310",
                    "--file-type",
                    "csv",
                ],
                {"exit_code": 0, "output_snippet": ""},
                id="proof of concept",
            ),
            pytest.param(
                [
                    "ahb",
                    "-p",
                    "17201",
                    "--format-version",
                    "FV2310",
                    "--file-type",
                    "csv",
                    "-y",
                ],
                {"exit_code": 0, "output_snippet": ""},
                id="test assume yes",
            ),
        ],
    )
    def test_cli_pruefi_with_valid_arguments(
        self,
        argument_options: list[str],
        expected_response: dict[str, Union[str, int]],
    ) -> None:
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
        response = runner.invoke(app, argument_options)

        assert response.exit_code == expected_response.get("exit_code")
