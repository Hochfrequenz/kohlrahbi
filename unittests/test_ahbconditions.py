import json
from pathlib import Path

import pytest

from kohlrahbi.ahbtable.ahbcondtions import AhbConditions
from unittests import path_to_test_files_fv2310


class TestAhbConditions:
    def test_dump_as_json(self):
        test_condition_dict = AhbConditions(
            conditions_dict={
                "PARTIN": {
                    "2": "Condition2",
                    "3": "Condition3",
                },
                "COMDIS": {
                    "12": "Condition12",
                    "13": "Condition13",
                },
            }
        )
        expected_condition_dict = {
            "PARTIN": [
                {"condition_key": "2", "condition_text": "Condition2", "edifact_format": "PARTIN"},
                {"condition_key": "3", "condition_text": "Condition3", "edifact_format": "PARTIN"},
            ],
            "COMDIS": [
                {"condition_key": "12", "condition_text": "Condition12", "edifact_format": "COMDIS"},
                {"condition_key": "13", "condition_text": "Condition13", "edifact_format": "COMDIS"},
            ],
        }

        actual_output_dir = path_to_test_files_fv2310 / Path("actual-output/temp")

        test_condition_dict.dump_as_json(actual_output_dir)

        for edifact_format in ["PARTIN", "COMDIS"]:
            assert Path(actual_output_dir / edifact_format / "conditions.json").exists()
            with open(actual_output_dir / edifact_format / "conditions.json", "r", encoding="utf-8") as file:
                actual_package_dict = json.load(file)
                assert actual_package_dict == expected_condition_dict[edifact_format]

    @pytest.mark.parametrize(
        "dict1, dict2, expected",
        [
            pytest.param(
                {"UTILMD": {"1": "Condition1"}},
                {"COMDIS": {"2": "Condition2"}},
                {"UTILMD": {"1": "Condition1"}, "COMDIS": {"2": "Condition2"}},
                id="two different formats",
            ),
            pytest.param(
                {"UTILMD": {"1": "Condition1"}},
                {"UTILMD": {"1": "longer Condition1"}},
                {"UTILMD": {"1": "longer Condition1"}},
                id="same but longer condition",
            ),
            pytest.param(
                {"UTILMD": {"1": "Condition1"}},
                {},
                {"UTILMD": {"1": "Condition1"}},
                id="one empty",
            ),
        ],
    )
    def test_include_condition_dict(self, dict1, dict2, expected):
        test_condition_dict = AhbConditions(conditions_dict=dict1)
        test_condition_dict.include_condition_dict(dict2)
        assert test_condition_dict.conditions_dict == expected
