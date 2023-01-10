from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from kohlrahbi.harvester import harvest

runner: CliRunner = CliRunner()


class TestCli:
    @pytest.mark.parametrize(
        "pruefis, input_folder_name, output_folder_name, expected_response",
        [
            pytest.param(
                "11016",
                "/invalid-input-path",
                "",  # if the folder name is empty, the path will point on the temporary directory which is created by datafiles -> valid path
                {"exit_code": 2, "output_snippet": "'/invalid-input-path' does not exist"},
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
    def test_harvester_cli_with_invalid_arguments(
        self, datafiles, pruefis, input_folder_name: str, output_folder_name: str, expected_response
    ):
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
        response = runner.invoke(harvest, argument_options)

        assert response.exit_code == expected_response.get("exit_code")
        assert expected_response.get("output_snippet") in response.output

    @pytest.mark.datafiles(
        "./unittests/docx_files/UTILMDAHBWiM-informatorischeLesefassung3.1eKonsolidierteLesefassungmitFehlerkorrekturenStand25.10.2022_20230930_20221025.docx"
    )
    @pytest.mark.parametrize(
        "pruefis, input_folder_name, output_folder_name, expected_response",
        [
            pytest.param(
                "11016",
                "",
                "",
                {"exit_code": 0, "output_snippet": ""},
                id="proof of concept",
            ),
        ],
    )
    def test_harvester_cli_with_valid_arguments(
        self, datafiles, pruefis, input_folder_name: str, output_folder_name: str, expected_response
    ):

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
        response: Result = runner.invoke(harvest, argument_options)

        assert response.exit_code == expected_response.get("exit_code")
        assert expected_response.get("output_snippet") in response.output
