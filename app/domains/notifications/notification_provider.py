class MockNotificationProvider:
    name = "mock"

    def send(self, *, channel: str, user_id: str, title: str, message: str, payload: dict):
        if channel not in ["in_app", "email", "push"]:
            return {
                "status": "FAILED",
                "reason": "UNSUPPORTED_CHANNEL",
                "provider": self.name,
            }

        return {
            "status": "DELIVERED",
            "reason": "MOCK_DELIVERY",
            "provider": self.name,
            "external": False,
        }


class ExternalNotificationBoundaryProvider:
    name = "external_boundary"

    def send(self, *, channel: str, user_id: str, title: str, message: str, payload: dict):
        return {
            "status": "PROVIDER_NOT_CONFIGURED",
            "reason": "External notification provider is disabled until explicitly configured.",
            "provider": self.name,
            "external": True,
        }
