from app.domains.commerce_ingestion.execution import FeedExecutionService


def test_rc113_execute_valid_feed():
    service = FeedExecutionService()
    job = service.create_job(source_id="src", adapter_type="json", requested_by="admin")
    result = service.execute_job(
        job_id=job["job_id"],
        content='[{"external_offer_id":"1","product_title":"Laptop","product_url":"https://x.test","price":999,"currency":"EUR"}]',
    )
    assert result["executed"] is True
    assert result["job"]["ingested_count"] == 1
    assert result["job"]["failed_count"] == 0
