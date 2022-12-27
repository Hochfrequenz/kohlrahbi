import pytest

from kohlrahbi.harvester import get_valid_pruefis


@pytest.mark.parametrize(
    "input_pruefis, expected_pruefis",
    [
        pytest.param(
            ["11042", "13007"],
            ["11042", "13007"],
            id="only valid pruefis",
        ),
        pytest.param(
            ["01042", "13007"],
            ["13007"],
            id="invalid pruefi: leading zero",
        ),
        pytest.param(
            ["1042", "13007"],
            ["13007"],
            id="invalid pruefi: only four digits",
        ),
        pytest.param(
            ["abc", "13007"],
            ["13007"],
            id="invalid pruefi: characters",
        ),
        pytest.param(
            ["abc"],
            [],
            id="invalid pruefi: empty result",
        ),
    ],
)
def test_get_only_valid_pruefis(input_pruefis, expected_pruefis):
    valid_pruefis = get_valid_pruefis(list_of_pruefis=input_pruefis)
    assert valid_pruefis == expected_pruefis
