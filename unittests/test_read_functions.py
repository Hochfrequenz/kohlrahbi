import json
from pathlib import Path

import docx
import pytest  # type:ignore[import]
from docx import Document
from maus.edifact import EdifactFormat, EdifactFormatVersion

from kohlrahbi.ahb import get_pruefi_to_file_mapping
from kohlrahbi.ahbtable.ahbcondtions import AhbConditions
from kohlrahbi.ahbtable.ahbpackagetable import AhbPackageTable
from kohlrahbi.conditions import find_all_files_from_all_pruefis
from kohlrahbi.read_functions import get_all_conditions_from_doc, is_item_package_heading
from unittests import path_to_test_edi_energy_mirror_repo, path_to_test_files_fv2310


def create_heading_paragraph(text, style):
    paragraph = Document().add_paragraph(text)
    paragraph.style = style
    return paragraph


class TestReadFunctions:
    @pytest.mark.parametrize(
        "item, style_name, expected_boolean",
        [
            pytest.param(
                create_heading_paragraph("Übersicht der Pakete in der UTILMD", "Heading 1"),
                "Heading 1",
                True,
                id="heading1_valid",
            ),
            pytest.param(
                create_heading_paragraph("Übersicht der Pakete in der UTILMD", "Heading 2"),
                "Heading 2",
                True,
                id="heading2_valid",
            ),
            pytest.param(
                create_heading_paragraph("Übersicht der Pakete in der UTILMD", "Heading 3"),
                "Heading 3",
                False,
                id="invalid_style",
            ),
            pytest.param(
                create_heading_paragraph("Übersicht der Pakete in der IFSTA", "Heading 2"),
                "Heading 2",
                False,
                id="invalid_edifact_format",
            ),
            pytest.param(
                Document().add_table(rows=1, cols=1),
                "Heading 2",
                False,
                id="table_invalid",
            ),
        ],
    )
    def test_is_package_item_heading(self, item, style_name, expected_boolean):
        assert is_item_package_heading(item, style_name, EdifactFormat.UTILMD) == expected_boolean

    def test_get_all_conditions_from_doc(self):
        expected_output_dir = path_to_test_files_fv2310 / "expected-output"

        path_to_file = path_to_test_files_fv2310
        pruefi_to_file_mapping = get_pruefi_to_file_mapping(
            path_to_test_edi_energy_mirror_repo, EdifactFormatVersion.FV2310
        )

        collected_conditions: AhbConditions = AhbConditions()
        collected_packages: AhbPackageTable = AhbPackageTable()
        all_format_files = find_all_files_from_all_pruefis(pruefi_to_file_mapping)
        for edifact_format, files in all_format_files.items():
            for file in files:
                # type: ignore[call-arg, arg-type]
                doc = docx.Document(path_to_test_edi_energy_mirror_repo / path_to_file / Path(file))
                assert doc
                packages, cond_table = get_all_conditions_from_doc(doc, edifact_format)
                if packages.table is not None:
                    collected_conditions.include_condition_dict(packages.provide_conditions(edifact_format))
                collected_conditions.include_condition_dict(cond_table.conditions_dict)
                collected_packages.include_package_dict(packages.package_dict)

            expected_output_dict_path = expected_output_dir / Path(str(edifact_format))
            with open(expected_output_dict_path / Path("conditions.json"), "r", encoding="utf-8") as file:
                expected_cond_dict = json.load(file)
            expected_cond_dict = {item["condition_key"]: item["condition_text"] for item in expected_cond_dict}
            assert collected_conditions.conditions_dict[edifact_format] == expected_cond_dict
            if edifact_format in collected_packages.package_dict.keys():
                with open(expected_output_dict_path / Path("packages.json"), "r", encoding="utf-8") as file:
                    expected_package_dict = json.load(file)
                expected_package_dict = {
                    item["package_key"][:-1]: item["package_expression"] for item in expected_package_dict
                }
                assert collected_packages.package_dict[edifact_format] == expected_package_dict
