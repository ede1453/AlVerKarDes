from app.domains.llm_retry_policy.timeout_classifier import TimeoutClassifier


def test_timeout_classifier_marks_timeout_status():
    assert TimeoutClassifier().classify(latency_ms=10, timeout_ms=100, status="TIMEOUT") == "TIMEOUT"


def test_timeout_classifier_marks_near_timeout():
    assert TimeoutClassifier().classify(latency_ms=90, timeout_ms=100) == "NEAR_TIMEOUT"


def test_timeout_classifier_marks_within_timeout():
    assert TimeoutClassifier().classify(latency_ms=20, timeout_ms=100) == "WITHIN_TIMEOUT"
