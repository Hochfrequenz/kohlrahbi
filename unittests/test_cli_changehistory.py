"""
This module contains the tests for the CLI tool changehistory.
"""

from pathlib import Path

import pandas as pd
from click.testing import CliRunner, Result
from freezegun import freeze_time

from kohlrahbi.changehistory.command import changehistory

runner: CliRunner = CliRunner()

path_to_test_files: Path = Path(__file__).parent / "test-files"
path_to_test_files_fv2310 = path_to_test_files / Path("FV2310")


def are_excel_files_equal(actual_change_history_file, expected_change_history_file):
    """
    Compare two Excel files with multiple sheets.

    Args:
    file1 (str): The path to the first Excel file.
    file2 (str): The path to the second Excel file.

    Returns:
    bool: True if the files are identical, False otherwise.
    """
    xls1 = pd.ExcelFile(actual_change_history_file)
    xls2 = pd.ExcelFile(expected_change_history_file)

    if len(xls1.sheet_names) != len(xls2.sheet_names):
        return False

    for sheet in xls1.sheet_names:
        df1 = pd.read_excel(actual_change_history_file, sheet_name=sheet)
        df2 = pd.read_excel(expected_change_history_file, sheet_name=sheet)

        if not df1.equals(df2):
            return False

    return True


class TestCliChangeHistory:
    """
    Test the CLI tool changehistory.
    """

    @freeze_time("2024-03-30")
    def test_cli_changehistory(self):
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
        response: Result = runner.invoke(changehistory, argument_options)

        assert response.exit_code == 0

        timestamp_of_expected_change_history_file = "2024-03-30"
        change_history_file_name = f"{timestamp_of_expected_change_history_file}_change_histories.xlsx"
        assert Path(actual_output_dir, change_history_file_name).exists(), "No matching file found"

        path_to_actual_change_history_file = actual_output_dir / change_history_file_name
        path_to_expected_change_history_file = expected_output_dir / change_history_file_name

        assert are_excel_files_equal(
            actual_change_history_file=path_to_actual_change_history_file,
            expected_change_history_file=path_to_expected_change_history_file,
        )

        # Delete the change history files after the test
        path_to_actual_change_history_file.unlink(missing_ok=True)
