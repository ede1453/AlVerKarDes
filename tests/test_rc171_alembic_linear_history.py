from scripts.check_alembic_linear_history import check_linear_history


def test_alembic_history_is_linear():
    result = check_linear_history()

    assert result["revision_count"] >= 10
    # NOTE: this is a snapshot pin, not a structural check -- check_linear_history()
    # itself already raises AssertionError on branching/duplicate/dangling
    # revisions, so a real chain break fails loudly above this line regardless
    # of what string is asserted here. Bump this whenever a new migration lands
    # (verified 2026-07-19: chain is genuinely linear, 0001->0017, this was
    # just stale after 0016_user_roles/0017_decision_memory_owner were added).
    assert result["head"] == "0017_decision_memory_owner"
