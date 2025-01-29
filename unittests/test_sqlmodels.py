"""
we try to fill a database using kohlrahbi[sqlmodels] and the data from the machine-readable AHB submodule
"""

import json
from pathlib import Path
from typing import Generator

import pytest
from efoli import EdifactFormat, EdifactFormatVersion
from sqlmodel import Session, SQLModel, create_engine, select

from kohlrahbi.ahb import process_pruefi
from kohlrahbi.enums.ahbexportfileformat import AhbExportFileFormat
from kohlrahbi.models.sqlmodels.anwendungshandbuch import AhbLine, AhbMetaInformation, FlatAnwendungshandbuch


@pytest.fixture()
def sqlite_session(tmp_path: Path) -> Generator[Session, None, None]:
    database_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{database_path}")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(bind=engine) as session:
        yield session


def _load_flat_ahb_to_db(
    session: Session, json_path: Path, edifact_format: EdifactFormat, edifact_format_version: EdifactFormatVersion
) -> str:
    """returns the pruefi"""
    # you may use this kind of function to eventually load _all_ AHBs into a DB
    # if you e.g. check out our machine-readable AHB repository,
    #  for json_path in _mr_ahb_submodule_path.rglob("FV*/**/*.json"):
    #      with open(json_path, "r", encoding="utf-8") as json_file:
    #          edifact_format = EdifactFormat(json_path.parent.parent.name)
    #          edifact_format_version = EdifactFormatVersion(json_path.parent.parent.parent.name)
    #          _load_flat_ahb_to_db(...)
    with open(json_path, "r", encoding="utf-8") as json_file:
        file_body = json.loads(json_file.read())
        flat_ahb = FlatAnwendungshandbuch.model_validate(file_body)
        edifact_format = EdifactFormat.UTILMD
        edifact_format_version = EdifactFormatVersion.FV2504
        file_body["meta"]["edifact_format"] = str(edifact_format)
        file_body["meta"]["edifact_format_version"] = str(edifact_format_version)
        meta = AhbMetaInformation.model_validate(file_body["meta"])
        session.add(meta)
        flat_ahb.meta = meta
        for line_index, raw_line in enumerate(file_body["lines"]):
            raw_line["position_inside_ahb"] = line_index
            line = AhbLine.model_validate(raw_line)
            flat_ahb.lines.append(line)
            session.add(line)
        session.add(flat_ahb)
        session.commit()
    session.flush()
    return meta.pruefidentifikator


def test_sqlmodels(sqlite_session: Session, tmp_path: Path) -> None:
    flat_ahb_dir_path = tmp_path
    docx_file_path = (
        Path(__file__).parent.parent
        / "edi_energy_mirror"
        / "edi_energy_de"
        / "FV2504"
        / "UTILMDAHBStrom-informatorischeLesefassung2.1_99991231_20250404.docx"
    )
    process_pruefi("55001", docx_file_path, flat_ahb_dir_path, (AhbExportFileFormat.FLATAHB,))
    flat_ahb_path = flat_ahb_dir_path / "UTILMD" / "flatahb" / "55001.json"
    assert flat_ahb_path.exists()
    pruefi = _load_flat_ahb_to_db(sqlite_session, flat_ahb_path, EdifactFormat.UTILMD, EdifactFormatVersion.FV2504)
    ahbs_from_db = sqlite_session.exec(
        select(FlatAnwendungshandbuch)
        .join(AhbMetaInformation, FlatAnwendungshandbuch.id == AhbMetaInformation.ahb_id)  # type:ignore[arg-type]
        .join(AhbLine, FlatAnwendungshandbuch.id == AhbLine.ahb_id)  # type:ignore[arg-type]
        .where(AhbMetaInformation.pruefidentifikator == "55001")
    ).all()
    ahb_from_db: FlatAnwendungshandbuch = ahbs_from_db[0]
    assert isinstance(ahb_from_db, FlatAnwendungshandbuch)
    assert any(ahb_from_db.lines)
    assert ahb_from_db.meta is not None
    assert ahb_from_db.meta.pruefidentifikator == pruefi
