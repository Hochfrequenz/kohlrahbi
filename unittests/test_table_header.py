"""
Test the table_header module.
"""

import pytest

from kohlrahbi.table_header import create_mapping_of_tabstop_positions


@pytest.mark.parametrize(
    "initial, current, expected",
    [
        pytest.param([10, 20, 30], [15, 25, 35], {15: 10, 25: 20, 35: 30}, id="normal_operation"),
        pytest.param([], [], {}, id="empty_lists"),
        pytest.param([10, 20], [12, 22, 32], {12: 10, 22: 20, 32: 20}, id="unequal_lengths"),
        pytest.param([10, 20, 30], [10, 20, 30], {10: 10, 20: 20, 30: 30}, id="identical_lists"),
    ],
)
def test_create_mapping(initial, current, expected):
    """
    Test the create_mapping_of_tabstop_positions function.
    """
    assert create_mapping_of_tabstop_positions(initial, current) == expected


@pytest.mark.parametrize(
    "initial, current",
    [
        pytest.param([float("inf"), 200, 300], [float("inf"), 2, 3], id="no_possible_match"),
    ],
)
def test_create_mapping_error(initial, current):
    """
    Test the create_mapping_of_tabstop_positions function with an error.

    The error is a bit artificial and should not occur in real life.
    """
    with pytest.raises(ValueError):
        create_mapping_of_tabstop_positions(initial, current)
