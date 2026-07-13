from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domains.deal_storage.sqlalchemy_models import DealStorageBase
from app.domains.deal_storage.sqlalchemy_repository import SQLAlchemyDealStorageRepository


def make_repo():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    DealStorageBase.metadata.create_all(engine)
    session = Session(engine)
    return SQLAlchemyDealStorageRepository(session), session


def test_rc170_sqlalchemy_upsert_and_version():
    repo, session = make_repo()
    first = repo.upsert_record(
        deal_id="deal-1",
        payload={"status":"DISCOVERED"},
    )
    session.commit()
    second = repo.upsert_record(
        deal_id="deal-1",
        payload={"status":"VALIDATED"},
        expected_version=1,
    )
    session.commit()
    assert first["record"]["version"] == 1
    assert second["record"]["version"] == 2


def test_rc170_version_conflict():
    repo, session = make_repo()
    repo.upsert_record(
        deal_id="deal-1",
        payload={"status":"DISCOVERED"},
    )
    session.commit()
    result = repo.upsert_record(
        deal_id="deal-1",
        payload={"status":"VALIDATED"},
        expected_version=99,
    )
    assert result["persisted"] is False
    assert result["reason"] == "VERSION_CONFLICT"
