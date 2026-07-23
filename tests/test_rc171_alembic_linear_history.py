from scripts.check_alembic_linear_history import check_linear_history


def test_alembic_history_is_linear():
    result = check_linear_history()

    assert result["revision_count"] >= 10
    # NOTE: this is a snapshot pin, not a structural check -- check_linear_history()
    # itself already raises AssertionError on branching/duplicate/dangling
    # revisions, so a real chain break fails loudly above this line regardless
    # of what string is asserted here. Bump this whenever a new migration lands
    # (verified 2026-07-23: chain is genuinely linear, 0001->0023, this was
    # just stale after 0023_provider_schedules was added, also verified clean
    # end-to-end on a fresh throwaway database plus a downgrade/upgrade
    # roundtrip, not just this structural check).
    assert result["head"] == "0023_provider_schedules"
