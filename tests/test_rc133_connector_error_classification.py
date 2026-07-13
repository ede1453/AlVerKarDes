from app.domains.commerce_ingestion.http_execution import (
    ConnectorErrorClassifier,
)


def test_rc133_error_classification():
    classifier = ConnectorErrorClassifier()
    assert classifier.classify(
        status_code=429
    )["retryable"] is True
    assert classifier.classify(
        status_code=403
    )["retryable"] is False
    assert classifier.classify(
        status_code=503
    )["category"] == "UPSTREAM_SERVER_ERROR"
