class TimeoutClassifier:
    def classify(self, *, latency_ms: int | None, timeout_ms: int | None, status: str | None = None) -> str:
        if status == "TIMEOUT":
            return "TIMEOUT"

        if timeout_ms is None or latency_ms is None:
            return "UNKNOWN"

        if latency_ms > timeout_ms:
            return "TIMEOUT"

        if latency_ms > timeout_ms * 0.8:
            return "NEAR_TIMEOUT"

        return "WITHIN_TIMEOUT"
