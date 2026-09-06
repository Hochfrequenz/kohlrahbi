from collections.abc import Callable
from pathlib import Path

import docx
import docx.table
import pytest

from unittests.cellparagraph import CellParagraph


@pytest.fixture(autouse=True)
def _disable_rich_color(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Force rich/typer CLI output to render without ANSI escape codes.
    Some environments (e.g. CI runners) set FORCE_COLOR, which makes rich treat output as a
    color-capable terminal even though typer.testing.CliRunner captures a non-tty stream. Rich
    then emits bold/dim styling around option names, splitting e.g. "--url" into separately
    escaped spans ("-" + "-url") and breaking plain substring assertions against CliRunner
    output. NO_COLOR alone does not prevent this, since bold/dim are style, not color - the
    terminal detection itself (driven by FORCE_COLOR) has to be neutralized.
    """
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.setenv("NO_COLOR", "1")


@pytest.fixture
def get_ahb_table_with_multiple_paragraphs() -> Callable[[list[CellParagraph]], docx.table.Table]:
    def _setup_ahb_table(body_cell_paragraphs: list[CellParagraph]) -> docx.table.Table:
        doc = docx.Document()
        table = doc.add_table(rows=1, cols=1)

        body_cell = table.rows[0].cells[0]

        # the cell comes with an empty paragraph which I could not delete.
        # So we insert the BodyCellParagraph attributes into the empty paragraph
        first_body_cell_paragprah: CellParagraph = body_cell_paragraphs[0]

        body_cell.paragraphs[0].text = first_body_cell_paragprah.text

        if first_body_cell_paragprah.tabstop_positions is not None:
            for tabstop_position in first_body_cell_paragprah.tabstop_positions:
                body_cell.paragraphs[0].paragraph_format.tab_stops.add_tab_stop(tabstop_position)

        body_cell.paragraphs[0].paragraph_format.left_indent = first_body_cell_paragprah.left_indent_length

        for paragraph_index, bcp in zip(
            range(1, len(body_cell_paragraphs[1:]) + 1), body_cell_paragraphs[1:], strict=False
        ):
            # add paragraph with text
            body_cell.add_paragraph(text=bcp.text)

            # set tabstop positions
            if bcp.tabstop_positions is not None:
                for tabstop_position in bcp.tabstop_positions:
                    body_cell.paragraphs[paragraph_index].paragraph_format.tab_stops.add_tab_stop(tabstop_position)

            # set left indent lenght
            body_cell.paragraphs[paragraph_index].paragraph_format.left_indent = bcp.left_indent_length

        result: docx.table.Table = table
        return result

    return _setup_ahb_table


# edi_energy_mirror is a private repository, so it is not available in every CI run: pull requests
# from forks get no secrets and therefore cannot fetch the submodule. These test modules read real
# documents from it - unlike the rest of the suite, which uses the miniature mirror committed under
# unittests/test-edi-energy-mirror-repo - so they are skipped instead of failing when it is absent.
# The list is the empirically determined set: without the submodule these 8 modules produce 36
# failures and no other module does.
_MODULES_REQUIRING_EDI_ENERGY_MIRROR = frozenset(
    {
        "test_ahb.py",
        "test_cli_changehistory_docx.py",
        "test_cli_conditions.py",
        "test_current_state.py",
        "test_docxfilefinder.py",
        "test_quality_map.py",
        "test_read_functions.py",
        "test_sqlmodels.py",
    }
)


def _edi_energy_mirror_is_available() -> bool:
    """Whether the edi_energy_mirror submodule is checked out and populated."""
    return (Path(__file__).parents[1] / "edi_energy_mirror" / "edi_energy_de").is_dir()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip the tests that need the private edi_energy_mirror submodule when it is unavailable."""
    if _edi_energy_mirror_is_available():
        return
    skip_marker = pytest.mark.skip(reason="the private edi_energy_mirror submodule is not available")
    for item in items:
        if Path(str(item.fspath)).name in _MODULES_REQUIRING_EDI_ENERGY_MIRROR:
            item.add_marker(skip_marker)
