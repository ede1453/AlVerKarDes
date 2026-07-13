from app.domains.deal_storage.service import DealStorageRepository


def test_rc167_dry_run_and_purge():
    repo = DealStorageRepository()
    repo.upsert(
        deal_id="old-deal",
        payload={"status":"ARCHIVED"},
        version=1,
        archived=True,
        persisted_at="2025-01-01T00:00:00+00:00",
    )
    dry = repo.purge_archived(
        older_than_days=30,
        reference_time="2026-07-12T00:00:00+00:00",
        dry_run=True,
    )
    assert dry["candidate_count"] == 1
    assert repo.get("old-deal") is not None

    real = repo.purge_archived(
        older_than_days=30,
        reference_time="2026-07-12T00:00:00+00:00",
        dry_run=False,
    )
    assert real["purged_count"] == 1
    assert repo.get("old-deal") is None
