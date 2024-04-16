"""
class which contains AHB package condition table
"""

import json
import re
from pathlib import Path

import attrs
import pandas as pd
from docx.table import Table as DocxTable  # type: ignore[import-untyped]
from maus.edifact import EdifactFormat
from pydantic import BaseModel, ConfigDict

from kohlrahbi.logger import logger

# pylint: disable=duplicate-code


class AhbPackageTable(BaseModel):
    """
    This class contains the AHB Package table as you see it in the beginning AHB documents,
    but in a machine readable format.
    """

    table: pd.DataFrame = None
    package_dict: dict[EdifactFormat, dict[str, str]] = {}
    model_config = ConfigDict(arbitrary_types_allowed=True)

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

    def provide_conditions(self, edifact_format: EdifactFormat) -> dict[EdifactFormat, dict[str, str]]:
        """collect conditions from package table and store them in conditions dict."""
        conditions_dict: dict[EdifactFormat, dict[str, str]] = {edifact_format: {}}

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
                assert all([match[1] is not None for match in matches])
                for match in matches:
                    # make text prettier:
                    text = match[1].strip()
                    text = re.sub(r"\s+", " ", text)

                    # check whether condition was already collected:
                    condition_key_not_collected_yet = conditions_dict[edifact_format].get(match[0]) is None
                    if not condition_key_not_collected_yet:
                        key_exits_but_shorter_text = len(text) > len(conditions_dict[edifact_format].get(match[0]))
                    if condition_key_not_collected_yet or key_exits_but_shorter_text:
                        conditions_dict[edifact_format][match[0]] = text

        logger.info("The package conditions for %s were collected.", edifact_format)
        return conditions_dict

    def provide_packages(self, edifact_format: EdifactFormat):
        """collect conditions from package table and store them in conditions dict."""
        package_dict: dict[EdifactFormat, dict[str, str]] = {edifact_format: {}}

        df = self.table
        there_are_packages = (df["Paket"] != "").any()
        if there_are_packages:
            for index, row in df.iterrows():
                package = row["Paket"]
                # Use re.search to find the first match
                match = re.search(r"\[(\d+)P\]", package)
                if not match:
                    raise ValueError("No valid package key found in the package column.")
                    # Extract the matched digits
                package = match.group(1)
                if package != "1":
                    package_conditions = row["Paketvoraussetzung(en)"].strip()
                    # check whether package was already collected:
                    package_key_not_collected_yet = package_dict[edifact_format].get(package) is None
                    if not package_key_not_collected_yet:
                        key_exits_but_shorter_text = len(package_conditions) > len(
                            package_dict[edifact_format].get(package)
                        )
                    if package_key_not_collected_yet or key_exits_but_shorter_text:
                        package_dict[edifact_format][package] = package_conditions

        logger.info("Packages for %s were collected.", edifact_format)
        self.package_dict = package_dict

    def include_package_dict(self, to_add=dict[EdifactFormat, dict[str, str]] | None) -> None:
        """ " Include a dict of conditions to the conditions_dict"""
        if to_add is None:
            logger.info("Packages dict to be added is empty.")
        for edifact_format, edi_cond_dict in to_add.items():
            for package_key, package_conditions in edi_cond_dict.items():
                if edifact_format in self.package_dict:
                    if package_key in self.package_dict[edifact_format]:
                        if len(package_conditions) > len(
                            self.package_dict[edifact_format][package_key]
                        ):  # +1 to avoid simple line breaks
                            self.package_dict[edifact_format][package_key] = package_conditions
                    else:
                        self.package_dict[edifact_format][package_key] = package_conditions
                else:
                    self.package_dict[edifact_format] = {package_key: package_conditions}

        logger.info("Packages were updated.")

    def dump_as_json(self, output_directory_path: Path) -> None:
        """
        Writes all collected packages to a json file.
        The file will be stored in the directory:
            'output_directory_path/<edifact_format>/conditions.json'
        """
        for edifact_format in self.package_dict.keys():
            package_json_output_directory_path = output_directory_path / str(edifact_format)
            package_json_output_directory_path.mkdir(parents=True, exist_ok=True)
            file_path = package_json_output_directory_path / "packages.json"
            # resort  PackageKeyConditionTextMappings for output
            sorted_package_dict = {
                k: self.package_dict[edifact_format][k] for k in sorted(self.package_dict[edifact_format], key=int)
            }
            array = [
                {"package_key": i + "P", "package_expression": sorted_package_dict[i], "edifact_format": edifact_format}
                for i in sorted_package_dict
            ]
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(array, file, ensure_ascii=False, indent=2)

            logger.info(
                "The package.json file for %s is saved at %s",
                edifact_format,
                file_path,
            )
