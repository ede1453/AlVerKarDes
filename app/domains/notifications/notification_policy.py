class NotificationPolicy:
    def __init__(self, allowed_channels: list[str] | None = None):
        self.allowed_channels = allowed_channels or ["in_app", "email", "push"]

    def evaluate(self, *, user_id: str, channel: str, title: str, message: str):
        warnings: list[str] = []

        if not user_id:
            return {"allowed": False, "reason": "MISSING_USER_ID", "warnings": warnings}

        if channel not in self.allowed_channels:
            return {"allowed": False, "reason": "UNSUPPORTED_CHANNEL", "warnings": warnings}

        if not title or not message:
            return {"allowed": False, "reason": "MISSING_NOTIFICATION_CONTENT", "warnings": warnings}

        if channel in ["email", "push"]:
            warnings.append("EXTERNAL_DELIVERY_BOUNDARY")

        return {"allowed": True, "reason": "ALLOWED", "warnings": warnings}
