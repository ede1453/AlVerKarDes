from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc232_category_quota():
    result = ConsumerTrustService().evaluate_category_quota(
        category="laptop",
        existing_count=2,
        maximum_count=3,
    )
    assert result["allowed"] is True
    assert result["remaining_count"] == 1
