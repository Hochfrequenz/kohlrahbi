from pathlib import Path

import pytest  # type:ignore[import]

from kohlrahbi.harvester import get_docx_files_which_may_contain_searched_pruefi


@pytest.mark.parametrize(
    "searched_pruefi, expected_docx_count",
    [
        pytest.param(
            "11042",
            6,
            id="11042 - Anmeldung MSB",
        ),
        pytest.param(
            "13002",
            1,
            id="13002 - Zaehlerstand (Gas)",
        ),
    ],
)
def test_docx_finder(searched_pruefi: str, expected_docx_count: int):

    path_to_ahb_documents: Path = Path.cwd() / Path("unittests/docx_files")

    paths_to_docx_files: list[Path] = get_docx_files_which_may_contain_searched_pruefi(
        searched_pruefi=searched_pruefi, path_to_ahb_documents=path_to_ahb_documents
    )

    assert len(paths_to_docx_files) == expected_docx_count
