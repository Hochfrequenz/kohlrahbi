"""This module contains the ahbconditions class."""

import json
import re
from pathlib import Path

from docx.table import Table as DocxTable
from maus.edifact import EdifactFormat
from pydantic import BaseModel, ConfigDict, Field

from kohlrahbi.logger import logger


class AhbConditions(BaseModel):
    """
    Class which contains a dict of conditions for each edifact format
    """

    conditions_dict: dict[EdifactFormat, dict[str, str]] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_docx_table(cls, docx_tables: list[DocxTable], edifact_format: EdifactFormat) -> "AhbConditions":
        """
        Create an AhbPackageTable object from a docx table.
        """
        table_data = []
        for table in docx_tables:
            for row in table.rows:
                if row.cells[-1].text and row.cells[0].text != "EDIFACT Struktur":
                    row_data = row.cells[-1].text
                    table_data.append(row_data)

        conditions_dict = {}
        are_there_conditions = len(table_data) > 0
        if are_there_conditions:
            conditions_dict = AhbConditions.collect_conditions(
                conditions_list=table_data, edifact_format=edifact_format
            )

        return cls(conditions_dict=conditions_dict)

    @staticmethod
    def collect_conditions(
        conditions_list: list[str], edifact_format: EdifactFormat
    ) -> dict[EdifactFormat, dict[str, str]]:
        """collect conditions from list of all conditions and store them in conditions dict."""
        conditions_dict: dict[EdifactFormat, dict[str, str]] = {edifact_format: {}}

        conditions_str = "".join(conditions_list)
        conditions_dict = parse_conditions_from_string(conditions_str, edifact_format, conditions_dict)
        logger.info("The package conditions for %s were collected.", edifact_format)
        return conditions_dict

    def include_condition_dict(self, to_add: dict[EdifactFormat, dict[str, str]] | None) -> None:
        """ " Include a dict of conditions to the conditions_dict"""
        if to_add is None:
            logger.info("Conditions dict to be added is empty.")
            return
        for edifact_format, edi_cond_dict in to_add.items():
            for condition_key, condition_text in edi_cond_dict.items():
                if edifact_format in self.conditions_dict:  # pylint:disable=unsupported-membership-test
                    if (
                        # pylint:disable=unsubscriptable-object
                        condition_key in self.conditions_dict[edifact_format]
                        and len(condition_text) > len(self.conditions_dict[edifact_format][condition_key])
                        # pylint:disable=unsubscriptable-object
                        or condition_key not in self.conditions_dict[edifact_format]
                    ):
                        self.conditions_dict[edifact_format][condition_key] = condition_text
                else:
                    self.conditions_dict[edifact_format] = {  # pylint:disable=unsupported-assignment-operation
                        condition_key: condition_text
                    }

        logger.info("Conditions were updated.")

    def dump_as_json(self, output_directory_path: Path) -> None:
        """
        Writes all collected conditions to a json file.
        The file will be stored in the directory:
            'output_directory_path/<edifact_format>/conditions.json'
        """
        # pylint:disable=no-member
        for edifact_format, format_cond_dict in self.conditions_dict.items():
            condition_json_output_directory_path = output_directory_path / str(edifact_format)
            condition_json_output_directory_path.mkdir(parents=True, exist_ok=True)
            file_path = condition_json_output_directory_path / "conditions.json"
            # resort ConditionKeyConditionTextMappings for output
            sorted_condition_dict = {k: format_cond_dict[k] for k in sorted(format_cond_dict, key=int)}
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


def parse_conditions_from_string(
    conditions_text: str, edifact_format: EdifactFormat, conditions_dict: dict[EdifactFormat, dict[str, str]]
) -> dict[EdifactFormat, dict[str, str]]:
    """
    Takes string with some conditions and sorts it into a dict.
    """
    # Split the input into parts enclosed in square brackets and other parts
    matches = re.findall(
        r"\[(\d+)](.*?)(?=\[\d+]|$)",
        conditions_text,
        re.DOTALL,
    )
    for match in matches:
        # make text prettier:
        text = match[1].strip()
        text = re.sub(r"\s+", " ", text)

        # check whether condition was already collected:
        existing_text = conditions_dict[edifact_format].get(match[0])
        is_condition_key_collected_yet = existing_text is not None
        key_exits_but_shorter_text = existing_text is not None and len(text) > len(existing_text)
        if not is_condition_key_collected_yet or key_exits_but_shorter_text:
            conditions_dict[edifact_format][match[0]] = text
    return conditions_dict
