import shutil
from pathlib import Path
from typing import Union

import pytest  # type:ignore[import]
from click.testing import CliRunner, Result

from kohlrahbi import main

runner: CliRunner = CliRunner()


class TestCli:
    """
    This class contains the unit tests for the CLI tool.
    """

    @pytest.mark.parametrize(
        "pruefis, input_folder_name, output_folder_name, expected_response",
        [
            pytest.param(
                "11016",
                "/invalid-input-path",
                "",  # if the folder name is empty, the path will point on the temporary directory which is created by datafiles -> valid path
                {"exit_code": 2, "output_snippet": "invalid-input-path' does not exist"},
                id="invalid input path",
            ),
            pytest.param(
                "11016",
                "",
                "/invalid/output/path",
                {"exit_code": 1, "output_snippet": "The output directory does not exist"},
                id="invalid output path",
            ),
            pytest.param(
                "abc",
                "",
                "",
                {"exit_code": 1, "output_snippet": "There are no valid pruefidentifkatoren"},
                id="invalid pruefidentifikator",
            ),
        ],
    )
    def test_kohlrahbi_cli_with_invalid_arguments(
        self, datafiles, pruefis, input_folder_name: str, output_folder_name: str, expected_response
    ):
        """
        This test runs the CLI tool with invalid arguments and checks if the output is as expected.
        """
        input_path: Path = Path(datafiles) / Path(input_folder_name)
        output_path: Path = Path(datafiles) / Path(output_folder_name)

        argument_options: list[str] = [
            "--pruefis",
            pruefis,
            "--input_path",
            str(input_path),
            "--output_path",
            str(output_path),
        ]

        # Call the CLI tool with the desired arguments
        response = runner.invoke(main, argument_options)

        assert response.exit_code == expected_response.get("exit_code")
        assert expected_response.get("output_snippet") in response.output

    @pytest.mark.datafiles(
        "./unittests/docx_files/UTILMDAHBWiM-informatorischeLesefassung3.1eKonsolidierteLesefassungmitFehlerkorrekturenStand25.10.2022_20230930_20221025.docx"
    )
    @pytest.mark.parametrize(
        "argument_options, input_folder_name, output_folder_name, expected_response",
        [
            pytest.param(
                [
                    "-p",
                    "11016",
                    "--file-type",
                    "csv",
                ],
                "",  # if the folder name is empty, the path will point on the temporary directory which is created by datafiles -> valid path
                "",  # if the folder name is empty, the path will point on the temporary directory which is created by datafiles -> valid path
                {"exit_code": 0, "output_snippet": ""},
                id="proof of concept",
            ),
            pytest.param(
                [
                    "-p",
                    "11016",
                    "--file-type",
                    "csv",
                    "-y",
                ],
                "",  # if the folder name is empty, the path will point on the temporary directory which is created by datafiles -> valid path
                "",  # if the folder name is empty, the path will point on the temporary directory which is created by datafiles -> valid path
                {"exit_code": 0, "output_snippet": ""},
                id="test assume yes",
            ),
        ],
    )
    def test_kohlrahbi_cli_with_valid_arguments(
        self,
        datafiles,
        input_folder_name: str,
        output_folder_name: str,
        argument_options: list[str],
        expected_response: dict[str, Union[str, int]],
    ):
        """
        This test runs the CLI tool with valid arguments and checks if the output is as expected.
        """

        input_path: Path = Path(datafiles) / Path(input_folder_name)
        output_path: Path = Path(datafiles) / Path(output_folder_name)

        argument_options.extend(["--input_path", str(input_path), "--output_path", str(output_path)])

        # Call the CLI tool with the desired arguments
        response: Result = runner.invoke(main, argument_options)

        assert response.exit_code == expected_response.get("exit_code")
        expected_output_snippet = expected_response.get("output_snippet")
        if expected_output_snippet is not None and isinstance(expected_output_snippet, str):
            assert expected_output_snippet in response.output
        else:
            assert False  # break the test if the output_snippet is None

        path_to_new_fancy_folder = Path("./output/new_and_fancy")
        if path_to_new_fancy_folder.exists() and path_to_new_fancy_folder.is_dir():
            shutil.rmtree(path_to_new_fancy_folder)
