from dataclasses import dataclass, field


@dataclass
class IntegrityCheck:
    name: str
    passed: bool
    count: int
    message: str


@dataclass
class DataIntegrityReport:
    passed: bool
    checks: list[IntegrityCheck] = field(default_factory=list)

    @property
    def failed_checks(self) -> list[IntegrityCheck]:
        return [check for check in self.checks if not check.passed]


class DataIntegrityGuard:
    async def run(self, repo) -> DataIntegrityReport:
        checks = [
            await self._check_active_offers_do_not_reference_deleted_products(repo),
            await self._check_no_duplicate_active_canonical_keys(repo),
        ]

        return DataIntegrityReport(
            passed=all(check.passed for check in checks),
            checks=checks,
        )

    async def _check_active_offers_do_not_reference_deleted_products(self, repo) -> IntegrityCheck:
        count = await repo.count_active_offers_for_deleted_products()
        return IntegrityCheck(
            name="active_offers_do_not_reference_deleted_products",
            passed=count == 0,
            count=count,
            message="Active offers must not point to soft-deleted products.",
        )

    async def _check_no_duplicate_active_canonical_keys(self, repo) -> IntegrityCheck:
        count = await repo.count_duplicate_active_canonical_keys()
        return IntegrityCheck(
            name="no_duplicate_active_canonical_keys",
            passed=count == 0,
            count=count,
            message="Active products should not share the same canonical_key.",
        )
