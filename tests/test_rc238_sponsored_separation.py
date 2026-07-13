from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc238_sponsored_separation():
    result = ConsumerTrustService().validate_sponsored_separation(
        sponsored=True,
        labeled_as_sponsored=True,
        ranking_influenced=False,
    )
    assert result["compliant"] is True
