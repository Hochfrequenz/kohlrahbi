import json
from pathlib import Path

import docx  # type: ignore[import-untyped]
from maus.edifact import EdifactFormatVersion

from kohlrahbi.ahb import get_pruefi_to_file_mapping
from kohlrahbi.ahbtable.ahbcondtions import AhbConditions
from kohlrahbi.ahbtable.ahbpackagetable import AhbPackageTable
from kohlrahbi.conditions import find_all_files_from_all_pruefis
from kohlrahbi.read_functions import get_all_conditions_from_doc
from unittests import path_to_test_edi_energy_mirror_repo, path_to_test_files_fv2310


class TestAhbConditions:
    def test_dump_as_json(self):
        expected_output_dir = path_to_test_files_fv2310 / "expected-output"
        actual_output_dir = path_to_test_files_fv2310 / "actual-output"

        path_to_file = path_to_test_files_fv2310
        pruefi_to_file_mapping = get_pruefi_to_file_mapping(
            path_to_test_edi_energy_mirror_repo, EdifactFormatVersion.FV2310
        )

        collected_conditions: AhbConditions = AhbConditions()
        collected_packages: AhbPackageTable = AhbPackageTable()
        all_format_files = find_all_files_from_all_pruefis(pruefi_to_file_mapping)
        for edifact_format, files in all_format_files.items():
            for file in files:
                doc = docx.Document(path_to_test_edi_energy_mirror_repo / path_to_file / Path(file))
                assert doc
                packages, cond_table = get_all_conditions_from_doc(doc, edifact_format)
                if packages.table is not None:
                    collected_conditions.include_condition_dict(packages.provide_conditions(edifact_format))
                collected_conditions.include_condition_dict(cond_table.conditions_dict)
                collected_packages.include_package_dict(packages.package_dict)

            expected_output_dict_path = expected_output_dir / Path(str(edifact_format))
            collected_conditions.dump_as_json(actual_output_dir)
            with open(expected_output_dict_path / Path("conditions.json"), "r", encoding="utf-8") as file:
                expected_cond_dict = json.load(file)
            with open(
                actual_output_dir / Path(str(edifact_format)) / Path("conditions.json"), "r", encoding="utf-8"
            ) as file:
                actual_cond_dict = json.load(file)
            assert actual_cond_dict == expected_cond_dict
