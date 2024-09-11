from pathlib import Path

import pytest
from freezegun import freeze_time

from kohlrahbi.ahb import (
    extract_pruefis_from_docx,
    find_pruefidentifikatoren,
    get_ahb_documents_path,
    save_pruefi_map_to_toml,
)
from unittests import path_to_test_edi_energy_mirror_repo, path_to_test_files_fv2310


@pytest.mark.snapshot
class TestAhb:
    def test_find_pruefidentifikatoren(self, snapshot):
        """
        test find_pruefidentifikatoren.
        """
        pruefis = find_pruefidentifikatoren(Path(__file__).parents[1] / "edi_energy_mirror/edi_energy_de/FV2310")
        assert pruefis == snapshot

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

    @freeze_time("2024-04-29")
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
