from pathlib import Path

import pytest

from kohlrahbi.ahb import (
    extract_pruefis_from_docx,
    find_pruefidentifikatoren,
    get_ahb_documents_path,
    save_pruefi_map_to_toml,
)
from unittests import path_to_test_edi_energy_mirror_repo, path_to_test_files_fv2310


class TestAhb:
    def test_extract_pruefis_from_docx(self) -> None:
        """
        extract_pruefis_from_docx.
        """
        input_path = path_to_test_files_fv2310 / Path(
            "COMDISAHB-informatorischeLesefassung1.0dKonsolidierteLesefassungmitFehlerkorrekturenStand19.06.2023_20230719_20231001.docx"
        )
        pruefis = extract_pruefis_from_docx(input_path)
        assert (
            "29001" in pruefis
            and pruefis["29001"]
            == "COMDISAHB-informatorischeLesefassung1.0dKonsolidierteLesefassungmitFehlerkorrekturenStand19.06.2023_20230719_20231001.docx"
        )
        assert (
            "29002" in pruefis
            and pruefis["29002"]
            == "COMDISAHB-informatorischeLesefassung1.0dKonsolidierteLesefassungmitFehlerkorrekturenStand19.06.2023_20230719_20231001.docx"
        )

    def test_find_pruefidentifikatoren(self):
        """
        test find_pruefidentifikatoren.
        """
        pruefis = find_pruefidentifikatoren(path_to_test_files_fv2310)
        assert (
            "29001" in pruefis
            and pruefis["29001"]
            == "COMDISAHB-informatorischeLesefassung1.0dKonsolidierteLesefassungmitFehlerkorrekturenStand19.06.2023_20230719_20231001.docx"
        )
        assert (
            "17201" in pruefis
            and pruefis["17201"] == "ORDERSORDRSPAHBMaBiS-informatorischeLesefassung2.2c_99991231_20231001.docx"
        )
        assert (
            "37001" in pruefis
            and pruefis["37001"]
            == "PARTINAHB-informatorischeLesefassung1.0cKonsolidierteLesefassungmitFehlerkorrekturenStand29.09.2023_20240402_20231001.docx"
        )

    def test_get_ahb_documents_path(self):
        """
        test get_ahb_documents_path.
        """
        ahb_documents_path = get_ahb_documents_path(path_to_test_edi_energy_mirror_repo, "FV2310")
        assert ahb_documents_path == path_to_test_files_fv2310
        expected_path = path_to_test_edi_energy_mirror_repo / "edi_energy_de" / Path("FV2210")
        with pytest.raises(FileNotFoundError) as exc_info:
            get_ahb_documents_path(path_to_test_edi_energy_mirror_repo, "FV2210")
        assert str(exc_info.value) == f"The specified path {expected_path.absolute()} does not exist."

    def test_save_pruefi_map_to_toml(self):
        """
        test save_pruefi_map_to_toml.
        """
        pruefis = {
            "29001": "file1.docx",
            "17201": "file2.docx",
            "37001": "file3.docx",
        }
        save_pruefi_map_to_toml(pruefis, "FV1910")
        expected_output_path = (
            Path(__file__).parents[1] / "src" / "kohlrahbi" / "cache" / "FV1910_pruefi_docx_filename_map.toml"
        )
        assert expected_output_path.exists()
        expected_pruefi_map = '[meta_data]\nupdated_on = 2024-04-29\n\n[pruefidentifikatoren]\n29001 = "file1.docx"\n17201 = "file2.docx"\n37001 = "file3.docx"\n'
        with open(expected_output_path, "r", encoding="utf-8") as f:
            actual_pruefi_map = f.read()
        assert actual_pruefi_map == expected_pruefi_map
        expected_output_path.unlink()
