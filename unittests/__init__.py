"""
This file is here, because this allows for best de-coupling of tests and application/library logic.
Further reading: https://docs.pytest.org/en/6.2.x/goodpractices.html#tests-outside-application-code
"""

from pathlib import Path

from efoli import EdifactFormat

path_to_test_edi_energy_mirror_repo: Path = Path(__file__).parent / "test-edi-energy-mirror-repo"
path_to_test_files_fv2310 = path_to_test_edi_energy_mirror_repo / "edi_energy_de" / Path("FV2310")
# list of pruefis to check against in test_current_state
current_state_pruefis = [
    "13002",
    "13014",
    "13023",
    "15002",
    "17002",
    "17010",
    "17114",
    "17129",
    "17201",
    "17208",
    "17301",
    "19002",
    "19007",
    "19016",
    "19103",
    "19120",
    "19131",
    "19204",
    "19301",
    "19302",
    "21002",
    "21010",
    "21015",
    "21030",
    "21039",
    "23001",
    "23009",
    "25001",
    "25003",
    "25004",
    "25006",
    "25009",
    "27001",
    "27003",
    "29001",
    "29002",
    "31001",
    "31003",
    "31007",
    "31011",
    "33004",
    "35001",
    "35004",
    "37000",
    "37002",
    "37005",
    "39000",
    "39002",
    "44001",
    "44005",
    "44009",
    "44016",
    "44023",
    "44040",
    "44053",
    "44103",
    "44105",
    "44112",
    "44117",
    "44138",
    "44140",
    "44148",
    "44163",
    "44180",
    "55003",
    "55009",
    "55014",
    "55035",
    "55041",
    "55062",
    "55074",
    "55075",
    "55077",
    "55081",
    "55086",
    "55093",
    "55105",
    "55115",
    "55127",
    "55147",
    "55157",
    "55182",
    "55200",
    "55213",
    "55555",
]
test_formats = [EdifactFormat.ORDCHG, EdifactFormat.ORDRSP, EdifactFormat.IFTSTA, EdifactFormat.IFTSTA]
