"""
This module contains the function to write the collected conditions to a json file.
"""

import json
from pathlib import Path

from kohlrahbi.logger import logger


def dump_conditions_json(output_directory_path: Path, already_known_conditions: dict) -> None:
    """
    Writes all collected conditions to a json file.
    The file will be stored in the directory:
        'output_directory_path/<edifact_format>/conditions.json'
    """
    for edifact_format in already_known_conditions:
        condition_json_output_directory_path = output_directory_path / str(edifact_format)
        condition_json_output_directory_path.mkdir(parents=True, exist_ok=True)
        file_path = condition_json_output_directory_path / "conditions.json"
        # resort  ConditionKeyConditionTextMappings for output
        sorted_condition_dict = {
            k: already_known_conditions[edifact_format][k]
            for k in sorted(already_known_conditions[edifact_format], key=int)
        }
        array = [
            {"condition_key": i, "condition_text": sorted_condition_dict[i], "edifact_format": edifact_format}
            for i in sorted_condition_dict
        ]
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(array, file, ensure_ascii=False, indent=2)

        logger.info(
            "The conditions.json file for %s is saved at %s",
            edifact_format,
            file_path,
        )
