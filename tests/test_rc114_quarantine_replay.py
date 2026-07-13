from app.domains.commerce_ingestion.execution import FeedExecutionService


def test_rc114_invalid_item_goes_to_quarantine_and_replays():
    service = FeedExecutionService()
    job = service.create_job(source_id="src", adapter_type="json", requested_by="admin")
    result = service.execute_job(
        job_id=job["job_id"],
        content='[{"external_offer_id":"1","product_title":"","product_url":"https://x.test","price":0,"currency":"EUR"}]',
    )
    assert result["job"]["failed_count"] == 1
    item = service.repository.list_quarantine()[0]
    replay = service.replay_quarantine(quarantine_id=item["quarantine_id"])
    assert replay["replayed"] is True
