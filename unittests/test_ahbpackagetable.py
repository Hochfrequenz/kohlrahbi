import json
import shutil
from pathlib import Path
from typing import Optional

import pytest

from kohlrahbi.ahbtable.ahbpackagetable import AhbPackageTable, extract_number
from unittests import path_to_test_files_fv2310


class TestAhbPackageTable:
    def test_dump_as_json(self, tmp_path):
        test_package_dict = AhbPackageTable(
            package_dict={
                "PARTIN": {
                    "2P": "[1]u[2]",
                    "3P": "[3]u[4]",
                },
                "COMDIS": {
                    "2P": "[10]u[12]",
                    "3P": "[13]u[14]",
                },
            }
        )
        expected_package_dict = {
            "PARTIN": [
                {"edifact_format": "PARTIN", "package_expression": "[1]u[2]", "package_key": "2P"},
                {"edifact_format": "PARTIN", "package_expression": "[3]u[4]", "package_key": "3P"},
            ],
            "COMDIS": [
                {"edifact_format": "COMDIS", "package_expression": "[10]u[12]", "package_key": "2P"},
                {"edifact_format": "COMDIS", "package_expression": "[13]u[14]", "package_key": "3P"},
            ],
        }

        actual_output_dir = tmp_path / Path("actual-output/temp")

        test_package_dict.dump_as_json(actual_output_dir)

        for edifact_format in ["PARTIN", "COMDIS"]:
            assert Path(actual_output_dir / edifact_format / "packages.json").exists()
            with open(actual_output_dir / edifact_format / "packages.json", "r", encoding="utf-8") as file:
                actual_package_dict = json.load(file)
                assert actual_package_dict == expected_package_dict[edifact_format]

    @pytest.mark.parametrize(
        "dict1, dict2, expected",
        [
            pytest.param(
                {"UTILMD": {"1": "[1]u[2]"}},
                {"COMDIS": {"2": "[3]u[2]"}},
                {"UTILMD": {"1": "[1]u[2]"}, "COMDIS": {"2": "[3]u[2]"}},
                id="two different formats",
            ),
            pytest.param(
                {"UTILMD": {"1": "[1]u[2]"}},
                {"UTILMD": {"1": "[1]u[2]u[3]"}},
                {"UTILMD": {"1": "[1]u[2]u[3]"}},
                id="same but longer package expression",
            ),
            pytest.param(
                {"UTILMD": {"1": "[1]u[2]"}},
                {},
                {"UTILMD": {"1": "[1]u[2]"}},
                id="one empty",
            ),
        ],
    )
    def test_include_package_dict(self, dict1, dict2, expected):
        test_package_dict = AhbPackageTable(package_dict=dict1)
        test_package_dict.include_package_dict(dict2)
        assert test_package_dict.package_dict == expected

    @pytest.mark.parametrize(
        "key, expected",
        [
            pytest.param("UB1", -99999, id="UB1"),
            pytest.param("UB10", -99990, id="UB10"),
            pytest.param("1P", 1, id="1P"),
            pytest.param("10P", 10, id="10P"),
            pytest.param("XYZ", float("inf"), id="XYZ"),
            pytest.param("UB", float("inf"), id="UB"),
        ],
    )
    def test_extract_number(self, key: str, expected: Optional[int]):
        assert extract_number(key) == expected
