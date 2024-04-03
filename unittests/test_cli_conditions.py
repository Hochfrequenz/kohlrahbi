"""
This module contains the tests for the CLI tool conditions.
"""

from pathlib import Path

from click.testing import CliRunner, Result
from freezegun import freeze_time

from kohlrahbi.conditions.command import conditions

runner: CliRunner = CliRunner()

path_to_test_files: Path = Path(__file__).parent / "test-files"
path_to_test_files_fv2310 = path_to_test_files / Path("FV2310")


class TestCliConditions:
    """
    Test the CLI tool conditions.
    """

    @freeze_time("2024-03-30")
    def test_cli_conditions(self):
        """
        This test runs the CLI tool with valid arguments and checks if the output is as expected.
        """

        actual_output_dir = path_to_test_files_fv2310 / "actual-output"
        expected_output_dir = path_to_test_files_fv2310 / "expected-output"

        argument_options: list[str] = [
            "--input-path",
            str(path_to_test_files_fv2310),
            "--output-path",
            str(actual_output_dir),
        ]

        # Call the CLI tool with the desired arguments
        response: Result = runner.invoke(conditions, argument_options)

        # assert response.exit_code == 0

        timestamp_of_expected_change_history_file = "2024-03-30"
        conditions_file_name = f"{timestamp_of_expected_change_history_file}_conditions.json"  # TODO change to correct file extension or delete this comment
        # assert Path(actual_output_dir, conditions_file_name).exists(), "No matching file found"

        path_to_actual_conditions_file = actual_output_dir / conditions_file_name
        path_to_expected_conditions_file = expected_output_dir / conditions_file_name

        # assert actual_conditions are equal to expected_conditions

        # optional
        # Delete the conditions files after the test
        path_to_actual_conditions_file.unlink(missing_ok=True)
