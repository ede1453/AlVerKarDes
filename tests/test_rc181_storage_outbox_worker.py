from app.domains.deal_storage.operations_runtime import StorageOperationsRuntime


def test_rc181_worker_run():
    service = StorageOperationsRuntime()
    result = service.run_outbox_worker(
        claimed_events=[
            {
                "event_id":"event-1",
                "aggregate_id":"deal-1",
                "event_type":"DEAL_UPDATED",
            },
            {
                "event_id":"event-2",
                "aggregate_id":"deal-2",
                "event_type":"DEAL_UPDATED",
            },
        ],
        provider_results={
            "event-1":True,
            "event-2":False,
        },
    )
    assert result["run"]["claimed_count"] == 2
    assert result["run"]["published_count"] == 1
    assert result["run"]["failed_count"] == 1
    assert result["run"]["status"] == "COMPLETED_WITH_ERRORS"
