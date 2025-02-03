"""Tests for the changehistory module."""

import pytest

from kohlrahbi.changehistory import extract_sheet_name


@pytest.mark.parametrize(
    "input_filename,expected_output",
    [
        (
            "AHB_COMDIS_1.0f_20250606_99991231_20250606_ooox_8871.docx",
            "AHB_COMDIS_1.0f",
        ),
        (
            "MIG_UTILMD_2.1e_20250606_99991231_20250131_xoxx_11449.docx",
            "MIG_UTILMD_2.1e",
        ),
        (
            "AHB_ORDERS_3.0a_20240401_99991231_20231215_xoxx_11449.docx",
            "AHB_ORDERS_3.0a",
        ),
        (
            "EBD_4.0b_20250606_20250131_20241215_xoxx_11449.docx",
            "EBD_4.0b",
        ),
    ],
)
def test_standard_ahb_mig_files(input_filename: str, expected_output: str) -> None:
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
        (
            "VERY_LONG_FILENAME_THAT_EXCEEDS_EXCEL_LIMIT_1.0f_20250606_99991231.docx",
            "VERY_LONG_FILENAME_THAT_EXC_1.0f",
        ),
        (
            "SUPER_DUPER_LONG_DOCUMENT_NAME_WITH_VERSION_2.1e.docx",
            "SUPER_DUPER_LONG_DOCUMEN_2.1e",
        ),
    ],
)
def test_long_names_truncation(input_filename: str, expected_output: str) -> None:
    """Test that long names are properly truncated to Excel's 31-character limit."""
    result = extract_sheet_name(input_filename)
    assert result == expected_output
    assert len(result) <= 31  # Excel's sheet name length limit


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
