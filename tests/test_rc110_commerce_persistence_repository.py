from app.domains.commerce_ingestion.persistence import CommercePersistenceRepository


def test_rc110_source_and_job_persistence():
    repo = CommercePersistenceRepository()
    repo.save_source({"source_id":"amazon-de","name":"Amazon Germany"})
    assert repo.get_source("amazon-de")["name"] == "Amazon Germany"
    job = repo.create_job(source_id="amazon-de", adapter_type="csv", requested_by="admin")
    assert repo.get_job(job["job_id"])["status"] == "PENDING"
