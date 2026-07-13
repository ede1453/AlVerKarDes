from app.domains.commerce_ingestion.persistence import CommercePersistenceRepository


def test_rc111_job_history_filters():
    repo = CommercePersistenceRepository()
    a = repo.create_job(source_id="a", adapter_type="csv", requested_by="admin")
    repo.create_job(source_id="b", adapter_type="json", requested_by="admin")
    repo.update_job(a["job_id"], status="COMPLETED")
    assert len(repo.list_jobs(source_id="a")) == 1
    assert len(repo.list_jobs(status="COMPLETED")) == 1
