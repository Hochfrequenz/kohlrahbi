"""Tests for the changehistory module."""

import pytest

from kohlrahbi.changehistory import extract_sheet_name


@pytest.mark.parametrize(
    "input_filename,expected_output",
    [
        pytest.param(
            "AHB_COMDIS_1.0f_20250606_99991231_20250606_oxox_11427.docx",
            "AHB_COMDIS_1.0f",
            id="AHB_COMDIS_1.0f",
        ),
        pytest.param(
            "AHB_CONTRL_2.4a_20250606_99991231_20241213_xoxx_11128.docx",
            "AHB_CONTRL_2.4a",
            id="AHB_CONTRL_2.4a",
        ),
        pytest.param(
            "AHB_IFTSTA_2.0g_20250606_99991231_20241213_xoxx_11132.docx",
            "AHB_IFTSTA_2.0g",
            id="AHB_IFTSTA_2.0g",
        ),
        pytest.param(
            "AHB_MSCONS_3.1f_20250606_99991231_20250606_ooox_9612.docx",
            "AHB_MSCONS_3.1f",
            id="AHB_MSCONS_3.1f",
        ),
        pytest.param(
            "AHB_ORDCHG_1.0a_20250606_99991231_20250606_ooox_11100.docx",
            "AHB_ORDCHG_1.0a",
            id="AHB_ORDCHG_1.0a",
        ),
        pytest.param(
            "AHB_ORDERS_1.0a_20250606_99991231_20250131_xoxx_11441.docx",
            "AHB_ORDERS_1.0a",
            id="AHB_ORDERS_1.0a",
        ),
        pytest.param(
            "AHB_ORDRSP_1.0a_20250606_99991231_20250606_ooox_11104.docx",
            "AHB_ORDRSP_1.0a",
            id="AHB_ORDRSP_1.0a",
        ),
        pytest.param(
            "AHB_PARTIN_1.0e_20250606_99991231_20250606_ooox_9819.docx",
            "AHB_PARTIN_1.0e",
            id="AHB_PARTIN_1.0e",
        ),
        pytest.param(
            "AHB_PRICAT_2.0e_20250606_99991231_20250606_ooox_9965.docx",
            "AHB_PRICAT_2.0e",
            id="AHB_PRICAT_2.0e",
        ),
        pytest.param(
            "AHB_QUOTES_1.0_20250606_99991231_20241213_xoxx_11146.docx",
            "AHB_QUOTES_1.0",
            id="AHB_QUOTES_1.0",
        ),
        pytest.param(
            "AHB_REMADV_2.5d_20250606_99991231_20250131_xoxx_11434.docx",
            "AHB_REMADV_2.5d",
            id="AHB_REMADV_2.5d",
        ),
        pytest.param(
            "AHB_REQOTE_1.0a_20250606_99991231_20250606_ooox_11109.docx",
            "AHB_REQOTE_1.0a",
            id="AHB_REQOTE_1.0a",
        ),
        pytest.param(
            "AHB_UTILMD_2.1_20250606_99991231_20241213_xoxx_11157.docx",
            "AHB_UTILMD_2.1",
            id="AHB_UTILMD_2.1",
        ),
        pytest.param(
            "AHB_UTILTS_1.0_20250606_99991231_20241213_xoxx_11164.docx",
            "AHB_UTILTS_1.0",
            id="AHB_UTILTS_1.0",
        ),
        pytest.param(
            "EBD_4.0b_20250606_99991231_20250131_xoxx_11425.docx",
            "EBD_4.0b",
            id="EBD_4.0b",
        ),
        pytest.param(
            "MIG_APERAK_2.1i_20250606_99991231_20250606_ooox_8671.docx",
            "MIG_APERAK_2.1i",
            id="MIG_APERAK_2.1i",
        ),
        pytest.param(
            "MIG_COMDIS_1.0e_20250606_99991231_20250606_ooox_8885.docx",
            "MIG_COMDIS_1.0e",
            id="MIG_COMDIS_1.0e",
        ),
        pytest.param(
            "MIG_IFTSTA_2.0f_20250606_99991231_20250606_ooox_9326.docx",
            "MIG_IFTSTA_2.0f",
            id="MIG_IFTSTA_2.0f",
        ),
        pytest.param(
            "MIG_INVOIC_2.8d_20250606_99991231_20250131_xoxx_11438.docx",
            "MIG_INVOIC_2.8d",
            id="MIG_INVOIC_2.8d",
        ),
        pytest.param(
            "MIG_ORDERS_1.4a_20250606_99991231_20241213_xoxx_11139.docx",
            "MIG_ORDERS_1.4a",
            id="MIG_ORDERS_1.4a",
        ),
        pytest.param(
            "MIG_ORDRSP_1.4_20250606_99991231_20250606_ooox_9797.docx",
            "MIG_ORDRSP_1.4",
            id="MIG_ORDRSP_1.4",
        ),
        pytest.param(
            "MIG_PARTIN_1.0e_20250606_99991231_20250606_ooox_9836.docx",
            "MIG_PARTIN_1.0e",
            id="MIG_PARTIN_1.0e",
        ),
        pytest.param(
            "MIG_PRICAT_2.0d_20250606_99991231_20250606_ooox_9982.docx",
            "MIG_PRICAT_2.0d",
            id="MIG_PRICAT_2.0d",
        ),
        pytest.param(
            "MIG_QUOTES_1.3a_20250606_99991231_20241213_xoxx_11155.docx",
            "MIG_QUOTES_1.3a",
            id="MIG_QUOTES_1.3a",
        ),
        pytest.param(
            "MIG_REQOTE_1.3b_20250606_99991231_20250606_ooox_10067.docx",
            "MIG_REQOTE_1.3b",
            id="MIG_REQOTE_1.3b",
        ),
        pytest.param(
            "MIG_UTILMD_S2.1_20250606_99991231_20250131_xoxx_11449.docx",
            "MIG_UTILMD_S2.1",
            id="MIG_UTILMD_S2.1",
        ),
        pytest.param(
            "MIG_UTILTS_1.1e_20250606_99991231_20241213_xoxx_11171.docx",
            "MIG_UTILTS_1.1e",
            id="MIG_UTILTS_1.1e",
        ),
        pytest.param(
            "allgemeinefestlegungeninformatorischelesefassung_6.1b_20250606_99991231_20250606_ooox_8638.docx",
            "Allgemeine_Festlegungen_6.1b",
            id="allgemeinefestlegungeninformatorischelesefassung_6.1b",
        ),
        pytest.param(
            "apiguidelineinformatorischelesefassung_1.0a_20250606_99991231_20250606_ooox_10824.docx",
            "API_Guideline_1.0a",
            id="apiguidelineinformatorischelesefassung_1.0a",
        ),
        pytest.param(
            "codelistederkonfigurationen_1.3b_20250606_99991231_20241213_xoxx_11124.docx",
            "CL_der_Konfigurationen_1.3b",
            id="codelistederkonfigurationen_1.3b",
        ),
    ],
)
def test_extract_sheet_name(input_filename: str, expected_output: str) -> None:
    """Test extraction of sheet names from standard AHB/MIG files."""
    assert extract_sheet_name(input_filename) == expected_output


@pytest.mark.parametrize(
    "input_filename,expected_output",
    [
        (
            "Entscheidungsbaum-DiagrammeundCodelisten-informatorischeLesefassung3.5.docx",
            "EBDs_CL_3.5",
        ),
        (
            "EntscheidungsbaumDiagrammeundCodelisten-informatorischeLesefassung2.1.docx",
            "EBDs_CL_2.1",
        ),
    ],
)
def test_entscheidungsbaum_files(input_filename: str, expected_output: str) -> None:
    """Test extraction of sheet names from Entscheidungsbaum files."""
    assert extract_sheet_name(input_filename) == expected_output


@pytest.mark.parametrize(
    "input_filename,expected_output",
    [
        ("SIMPLE_DOCUMENT.docx", "SIMPLE_DOCUMENT"),  # File with no version number
        ("AHB_TEST-SPECIAL_1.0.docx", "AHB_TEST-SPECIAL_1.0"),  # File with special characters
        ("MIG.TEST.DOC_2.1a.docx", "MIG.TEST.DOC_2.1a"),  # File with multiple dots
    ],
)
def test_special_cases(input_filename: str, expected_output: str) -> None:
    """Test special cases and edge cases."""
    assert extract_sheet_name(input_filename) == expected_output
