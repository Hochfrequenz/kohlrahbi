"""
class which contains AHB package condition table
"""

import json
import re
from pathlib import Path

import pandas as pd
from docx.table import Table as DocxTable
from maus.edifact import EdifactFormat
from pydantic import BaseModel, ConfigDict, Field

from kohlrahbi.ahbtable.ahbcondtions import parse_conditions_from_string
from kohlrahbi.logger import logger


class AhbPackageTable(BaseModel):
    """
    This class contains the AHB Package table as you see it in the beginning AHB documents,
    but in a machine readable format.
    Caution: if two PackageTables objects are combined so far only the package_dict field is updated.
    """

    table: pd.DataFrame = pd.DataFrame()
    package_dict: dict[EdifactFormat, dict[str, str]] = Field(default_factory=dict)
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
        there_are_conditions = (self.table["Bedingungen"] != "").any()
        if there_are_conditions:
            for conditions_text in self.table["Bedingungen"][self.table["Bedingungen"] != ""]:
                conditions_dict = parse_conditions_from_string(conditions_text, edifact_format, conditions_dict)
        logger.info("The package conditions for %s were collected.", edifact_format)
        return conditions_dict

    def provide_packages(self, edifact_format: EdifactFormat) -> None:
        """collect conditions from package table and store them in conditions dict."""
        package_dict: dict[EdifactFormat, dict[str, str]] = {edifact_format: {}}

        there_are_packages = (self.table["Paket"] != "").any()
        if there_are_packages:
            for _, row in self.table.iterrows():
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
                    existing_text = package_dict[edifact_format].get(package)
                    is_package_key_collected_yet = existing_text is not None
                    key_exits_but_shorter_text = existing_text is not None and len(package_conditions) > len(
                        existing_text
                    )
                    if not is_package_key_collected_yet or key_exits_but_shorter_text:
                        package_dict[edifact_format][package] = package_conditions

        logger.info("Packages for %s were collected.", edifact_format)
        self.package_dict = package_dict

    def include_package_dict(self, to_add: dict[EdifactFormat, dict[str, str]] | None) -> None:
        """Include a dict of conditions to the conditions_dict"""
        if to_add is None:
            logger.info("Packages dict to be added is empty.")
            return
        for edifact_format, edi_cond_dict in to_add.items():
            for package_key, package_conditions in edi_cond_dict.items():
                if edifact_format in self.package_dict:
                    if (
                        package_key in self.package_dict[edifact_format]
                        and len(package_conditions) > len(self.package_dict[edifact_format][package_key])
                        or package_key not in self.package_dict[edifact_format]
                    ):
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
        for edifact_format, format_pkg_dict in self.package_dict.items():
            package_json_output_directory_path = output_directory_path / str(edifact_format)
            package_json_output_directory_path.mkdir(parents=True, exist_ok=True)
            file_path = package_json_output_directory_path / "packages.json"
            # resort  PackageKeyConditionTextMappings for output
            sorted_package_dict = {k: format_pkg_dict[k] for k in sorted(format_pkg_dict, key=int)}
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
