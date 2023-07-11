import pytest  # type:ignore[import]

from kohlrahbi import get_valid_pruefis


@pytest.mark.parametrize(
    "input_pruefis, expected_pruefis, known_pruefis",
    [
        pytest.param(
            ["11042", "13007"],
            ["11042", "13007"],
            None,
            id="only valid pruefis",
        ),
        pytest.param(
            ["01042", "13007"],
            ["13007"],
            None,
            id="invalid pruefi: leading zero",
        ),
        pytest.param(
            ["1042", "13007"],
            ["13007"],
            None,
            id="invalid pruefi: only four digits",
        ),
        pytest.param(
            ["abc", "13007"],
            ["13007"],
            None,
            id="invalid pruefi: characters",
        ),
        pytest.param(
            ["abc"],
            [],
            None,
            id="invalid pruefi: empty result",
        ),
        pytest.param(
            ["11*"],
            ["11001", "11002", "11003"],
            ["11001", "11002", "11003", "12001", "12002", "12003", "13001", "13002", "13003"],
            id="wildcard at end",
        ),
        pytest.param(
            ["*1"],
            ["11001", "12001", "13001"],
            ["11001", "11002", "11003", "12001", "12002", "12003", "13001", "13002", "13003"],
            id="wildcard at begin",
        ),
        pytest.param(
            ["11*1"],
            ["11001"],
            ["11001", "11002", "11003", "12001", "12002", "12003", "13001", "13002", "13003"],
            id="wildcard in the middle",  # who should seriously want this?
        ),
    ],
)
def test_get_only_valid_pruefis(input_pruefis: list[str], expected_pruefis: list[str], known_pruefis: list[str] | None):
    valid_pruefis = get_valid_pruefis(list_of_pruefis=input_pruefis, all_known_pruefis=known_pruefis)
    assert valid_pruefis == expected_pruefis
