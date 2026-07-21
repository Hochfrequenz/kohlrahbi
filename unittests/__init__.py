"""
This file is here, because this allows for best de-coupling of tests and application/library logic.
Further reading: https://docs.pytest.org/en/6.2.x/goodpractices.html#tests-outside-application-code
"""

import re
from pathlib import Path

from efoli import EdifactFormat

_ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape codes from CLI output.
    Some environments make rich render `typer` --help text with color, which highlights option
    names as separately styled spans (e.g. "--url" becomes "-" + "-url" with a reset in between).
    That breaks plain substring assertions against CliRunner output, so strip escape codes first.
    """
    return _ANSI_ESCAPE_PATTERN.sub("", text)


path_to_test_edi_energy_mirror_repo: Path = Path(__file__).parent / "test-edi-energy-mirror-repo"
path_to_test_files_fv2310 = path_to_test_edi_energy_mirror_repo / "edi_energy_de" / Path("FV2310")
# list of pruefis to check against in test_current_state
# One representative pruefi per EDIFACT format for regression testing.
# This keeps the test suite fast while covering all formats.
current_state_pruefis = [
    "13002",  # MSCONS
    "15002",  # QUOTES
    "17002",  # ORDERS
    "19002",  # ORDRSP
    "21002",  # IFTSTA
    "25004",  # UTILTS
    "27001",  # PRICAT
    "31001",  # INVOIC
    "33004",  # REMADV
    "35001",  # REQOTE
    "37000",  # PARTIN
    "39000",  # ORDCHG
    "44001",  # UTILMDG
    "55003",  # UTILMDS
]
test_formats = [EdifactFormat.ORDCHG, EdifactFormat.ORDRSP, EdifactFormat.IFTSTA]
