"""
This file is here, because this allows for best de-coupling of tests and application/library logic.
Further reading: https://docs.pytest.org/en/6.2.x/goodpractices.html#tests-outside-application-code
"""

from pathlib import Path

path_to_test_files: Path = Path(__file__).parent / "test-edi-energy-mirror-repo"
path_to_test_files_fv2310 = path_to_test_files / "edi_energy_de" / Path("FV2310")
