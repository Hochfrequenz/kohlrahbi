import re

import attrs
import pandas as pd
from docx.table import Table as DocxTable
from maus.edifact import EdifactFormat

from kohlrahbi.logger import logger


@attrs.define(auto_attribs=True, kw_only=True)
class AhbPackageTable:
    """
    This class contains the AHB Package table as you see it in the beginning AHB documents, but in a machine readable format.
    """

    table: pd.DataFrame

    @classmethod
    def from_docx_table(cls, docx_tables: list[DocxTable]) -> "AhbPackageTable":
        """
        Create an AhbPackageTable object from a docx table.

        """
        table_data = []
        for table in docx_tables:
            for row in table.rows:
                row_data = [cell.text for cell in row.cells]
                table_data.append(row_data)

        headers = table_data[0]
        data = table_data[1:]
        df = pd.DataFrame(data, columns=headers)
        return cls(table=df)

    def collect_conditions(self, already_known_conditions: dict, edifact_format: EdifactFormat) -> None:
        if already_known_conditions.get(edifact_format) is None:
            already_known_conditions[edifact_format] = {}
        df = self.table
        there_are_conditions = (df["Bedingungen"] != "").any()
        if there_are_conditions:
            for conditions_text in df["Bedingungen"][df["Bedingungen"] != ""]:
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
                    condition_key_not_collected_yet = already_known_conditions[edifact_format].get(match[0]) is None
                    if not condition_key_not_collected_yet:
                        key_exits_but_shorter_text = len(text) > len(
                            already_known_conditions[edifact_format].get(match[0])
                        )
                    if condition_key_not_collected_yet or key_exits_but_shorter_text:
                        already_known_conditions[edifact_format][match[0]] = text

        logger.info("The package conditions for %s were collected.", edifact_format)
