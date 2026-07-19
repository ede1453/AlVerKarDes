"""One-time manual promotion of a user to SUPERADMIN (AUTH-006 Parça 1, ADR-005).

There is no role-management endpoint yet (out of scope per ADR-005's open
questions) -- the first SUPERADMIN has to be set directly against the
database. This script exists so that step is a reviewable, auditable command
instead of an ad-hoc `UPDATE users SET role = ...` typed into a psql shell.

Usage:
    python scripts/promote_superadmin.py someone@example.com
"""

from __future__ import annotations

import asyncio
import sys

from app.core.database import AsyncSessionLocal
from app.domains.identity.models import UserRole
from app.domains.identity.repository import UserRepository


async def promote(email: str) -> None:
    async with AsyncSessionLocal() as db:
        repository = UserRepository(db)
        user = await repository.get_by_email(email)

        if user is None:
            print(f"No user found with email {email!r}.", file=sys.stderr)
            raise SystemExit(1)

        previous_role = user.role
        if previous_role == UserRole.SUPERADMIN:
            print(f"{email} is already SUPERADMIN. No change made.")
            return

        user.role = UserRole.SUPERADMIN
        await db.commit()
        print(f"{email}: {previous_role.value} -> {UserRole.SUPERADMIN.value}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/promote_superadmin.py <email>", file=sys.stderr)
        raise SystemExit(2)

    asyncio.run(promote(sys.argv[1]))


if __name__ == "__main__":
    main()
