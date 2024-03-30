"""
This test will check if we get the same results during the refactoring process.
"""

import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Union

import pandas as pd
import pytest  # type:ignore[import]
from click.testing import CliRunner, Result

from kohlrahbi import main

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


runner: CliRunner = CliRunner()

path_to_test_files: Path = Path(__file__).parent / "test-files"
path_to_test_files_fv2310 = path_to_test_files / Path("FV2310")


def get_csv_paths(root_dir) -> list[Path]:
    """Walk through root_dir and return paths of all CSV files."""
    root_path = Path(root_dir)
    return [path for path in root_path.rglob("*.csv")]


def are_csv_files_equal(actual_file, expected_file) -> bool:
    """Read two CSV files into pandas DataFrames and compare them."""
    actual_df = pd.read_csv(actual_file)
    expected_df = pd.read_csv(expected_file)
    return actual_df.equals(expected_df)


def compare_csv_files(actual_output_dir: Path, expected_output_dir: Path):
    """
    Compare CSV files in expected-output and actual-output directories.
    """

    # Get paths of all CSV files in both directories
    path_to_actual_csv_files = get_csv_paths(actual_output_dir)
    path_to_expected_csv_files = get_csv_paths(expected_output_dir)

    differences = []
    for expected, actual in zip(path_to_expected_csv_files, path_to_actual_csv_files):
        if not are_csv_files_equal(expected, actual):
            differences.append((expected, actual))

    # Report differences
    if differences:
        for diff in differences:
            logging.error("Files %s and %s are different.", diff[0], diff[1])
        assert False
    else:
        logging.info("All files are the same.")
        assert True


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


# Assume the directory structure and file naming are mirrored in expected-output and actual-output


class TestCli:
    """
    This class contains the unit tests for the CLI tool.
    """

    @pytest.mark.parametrize(
        "argument_options, input_path, output_path, expected_response",
        [
            pytest.param(
                [
                    "--format-version",
                    "FV2310",
                    "--file-type",
                    "csv",
                ],
                path_to_test_files_fv2310,
                path_to_test_files_fv2310,
                {"exit_code": 0, "output_snippet": ""},
                id="proof of concept",
            )
        ],
    )
    def test_kohlrahbi_cli_with_valid_arguments(
        self,
        input_path: Path,
        output_path: Path,
        argument_options: list[str],
        expected_response: dict[str, Union[str, int]],
    ):
        """
        This test runs the CLI tool with valid arguments and checks if the output is as expected.
        """

        actual_output_dir = output_path / "actual-output"
        expected_output_dir = output_path / "expected-output"

        argument_options.extend(["--input-path", str(input_path), "--output-path", str(actual_output_dir)])

        # Call the CLI tool with the desired arguments
        response: Result = runner.invoke(main, argument_options)

        assert response.exit_code == expected_response.get("exit_code")
        expected_output_snippet = expected_response.get("output_snippet")
        if expected_output_snippet is not None and isinstance(expected_output_snippet, str):
            assert expected_output_snippet in response.output
        else:
            assert False  # break the test if the output_snippet is None

        # Check if the generated files are the same as the expected files

        compare_csv_files(
            actual_output_dir=actual_output_dir,
            expected_output_dir=expected_output_dir,
        )

        # path_to_new_fancy_folder = Path("./output/new_and_fancy")
        # if path_to_new_fancy_folder.exists() and path_to_new_fancy_folder.is_dir():
        #     shutil.rmtree(path_to_new_fancy_folder)

    def test_changehistory(self):
        """
        This test runs the CLI tool with the changehistory flavour and checks if the output is as expected.
        """

        actual_output_dir = path_to_test_files_fv2310 / "actual-output"
        expected_output_dir = path_to_test_files_fv2310 / "expected-output"

        argument_options: list[str] = [
            "--flavour",
            "changehistory",
            "--input-path",
            str(path_to_test_files_fv2310),
            "--output-path",
            str(actual_output_dir),
        ]

        # Call the CLI tool with the desired arguments
        response: Result = runner.invoke(main, argument_options)

        assert response.exit_code == 0
        current_timestamp = datetime.now(UTC).strftime("%Y-%m-%d")

        change_history_file_name = f"{current_timestamp}_change_histories.xlsx"
        assert Path(actual_output_dir, change_history_file_name).exists(), "No matching file found"

        path_to_actual_change_history_file = actual_output_dir / change_history_file_name
        path_to_expected_change_history_file = expected_output_dir / change_history_file_name

        assert are_excel_files_equal(
            actual_change_history_file=path_to_actual_change_history_file,
            expected_change_history_file=path_to_expected_change_history_file,
        )

        # Delete the change history files after the test
        path_to_actual_change_history_file.unlink(missing_ok=True)
