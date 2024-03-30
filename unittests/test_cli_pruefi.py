from typing import Union

import pytest  # type:ignore[import]
from click.testing import CliRunner, Result

from kohlrahbi.pruefis.command import pruefi
from unittests.test_current_state import path_to_test_files_fv2310

runner: CliRunner = CliRunner()


class TestCliPruefi:
    """
    This class contains the unit tests for the CLI tool.
    """

    @pytest.mark.parametrize(
        "argument_options, expected_response",
        [
            pytest.param(
                [
                    "--pruefis",
                    "11016",
                    "--input-path",
                    "/invalid/input/path",
                ],
                {"exit_code": 2, "output_snippet": "invalid/input/path' does not exist"},
                id="invalid input path",
            ),
            pytest.param(
                [
                    "--pruefis",
                    "11016",
                    "--input-path",
                    path_to_test_files_fv2310,
                    "--output-path",
                    "/invalid/output/path",
                ],
                {"exit_code": 1, "output_snippet": "The path /invalid/output/path does not exist"},
                id="invalid output path",
            ),
            pytest.param(
                [
                    "--pruefis",
                    "abc",
                    "--input-path",
                    path_to_test_files_fv2310,
                    "--output-path",
                    path_to_test_files_fv2310,
                ],
                {"exit_code": 1, "output_snippet": "There are no valid pruefidentifkatoren"},
                id="invalid pruefidentifikator",
            ),
        ],
    )
    def test_cli_pruefi_with_invalid_arguments(self, argument_options: list[str], expected_response):
        """
        This test runs the CLI tool with invalid arguments and checks if the output is as expected.
        """

        # Call the CLI tool with the desired arguments
        response = runner.invoke(pruefi, argument_options)

        assert response.exit_code == expected_response.get("exit_code")
        assert expected_response.get("output_snippet") in response.output

    @pytest.mark.parametrize(
        "argument_options, expected_response",
        [
            pytest.param(
                [
                    "-p",
                    "17201",
                    "--file-type",
                    "csv",
                ],
                {"exit_code": 0, "output_snippet": ""},
                id="proof of concept",
            ),
            pytest.param(
                [
                    "-p",
                    "17201",
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
    ):
        """
        This test runs the CLI tool with valid arguments and checks if the output is as expected.
        """

        actual_output_dir = path_to_test_files_fv2310 / "actual-output"
        expected_output_dir = path_to_test_files_fv2310 / "expected-output"

        argument_options.extend(
            ["--input-path", str(path_to_test_files_fv2310), "--output-path", str(actual_output_dir)]
        )

        # Call the CLI tool with the desired arguments
        response: Result = runner.invoke(pruefi, argument_options)

        assert response.exit_code == expected_response.get("exit_code")
        expected_output_snippet = expected_response.get("output_snippet")
        if expected_output_snippet is not None and isinstance(expected_output_snippet, str):
            assert expected_output_snippet in response.output
        else:
            assert False  # break the test if the output_snippet is None
