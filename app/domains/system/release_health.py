from dataclasses import dataclass, field


@dataclass
class ReleaseHealthCheck:
    name: str
    passed: bool
    data: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class ReleaseHealthReport:
    status: str
    passed: bool
    checks: list[ReleaseHealthCheck]

    @property
    def failed_checks(self) -> list[ReleaseHealthCheck]:
        return [check for check in self.checks if not check.passed]


class ReleaseHealthService:
    async def run(
        self,
        *,
        integrity_guard,
        integrity_repo,
        metadata: dict | None = None,
        duplicate_regression_guard=None,
        duplicate_regression_repo=None,
        notification_health_service=None,
        merge_candidate_health_service=None,
    ) -> ReleaseHealthReport:
        metadata = metadata or {}
        checks: list[ReleaseHealthCheck] = []

        checks.append(
            ReleaseHealthCheck(
                name="application_runtime",
                passed=True,
                data={
                    "service": metadata.get("service", "AI Consumer Intelligence"),
                    "environment": metadata.get("environment", "local"),
                },
            )
        )

        try:
            integrity_report = await integrity_guard.run(integrity_repo)
            checks.append(
                ReleaseHealthCheck(
                    name="data_integrity",
                    passed=integrity_report.passed,
                    data={
                        "checks": [
                            {
                                "name": item.name,
                                "passed": item.passed,
                                "count": item.count,
                                "message": item.message,
                            }
                            for item in integrity_report.checks
                        ]
                    },
                )
            )
        except Exception as exc:
            checks.append(ReleaseHealthCheck(name="data_integrity", passed=False, error=str(exc)))

        if duplicate_regression_guard and duplicate_regression_repo:
            try:
                regression_report = await duplicate_regression_guard.run(duplicate_regression_repo)
                checks.append(
                    ReleaseHealthCheck(
                        name="duplicate_product_regression",
                        passed=regression_report.passed,
                        data={
                            "active_product_count": regression_report.active_product_count,
                            "active_offer_product_count": regression_report.active_offer_product_count,
                            "deleted_product_count": regression_report.deleted_product_count,
                            "errors": regression_report.errors,
                        },
                    )
                )
            except Exception as exc:
                checks.append(ReleaseHealthCheck(name="duplicate_product_regression", passed=False, error=str(exc)))

        if notification_health_service:
            try:
                notification_report = await notification_health_service.check()
                checks.append(
                    ReleaseHealthCheck(
                        name=notification_report["name"],
                        passed=notification_report["passed"],
                        data=notification_report.get("data", {}),
                        error=notification_report.get("error"),
                    )
                )
            except Exception as exc:
                checks.append(ReleaseHealthCheck(name="notification_queue", passed=False, error=str(exc)))

        if merge_candidate_health_service:
            try:
                merge_candidate_report = await merge_candidate_health_service.check()
                checks.append(
                    ReleaseHealthCheck(
                        name=merge_candidate_report["name"],
                        passed=merge_candidate_report["passed"],
                        data=merge_candidate_report.get("data", {}),
                        error=merge_candidate_report.get("error"),
                    )
                )
            except Exception as exc:
                checks.append(ReleaseHealthCheck(name="merge_candidate_queue", passed=False, error=str(exc)))

        passed = all(check.passed for check in checks)

        return ReleaseHealthReport(
            status="OK" if passed else "FAILED",
            passed=passed,
            checks=checks,
        )