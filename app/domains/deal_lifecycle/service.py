from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DealLifecycleService:
    VALID_STATUSES = {
        "DISCOVERED",
        "VALIDATED",
        "RECOMMENDED",
        "ALERTED",
        "EXPIRED",
        "REJECTED",
        "ARCHIVED",
    }

    ALLOWED_TRANSITIONS = {
        "DISCOVERED": {"VALIDATED", "REJECTED", "EXPIRED"},
        "VALIDATED": {"RECOMMENDED", "REJECTED", "EXPIRED"},
        "RECOMMENDED": {"ALERTED", "EXPIRED", "ARCHIVED"},
        "ALERTED": {"EXPIRED", "ARCHIVED"},
        "EXPIRED": {"ARCHIVED"},
        "REJECTED": {"ARCHIVED"},
        "ARCHIVED": set(),
    }

    def __init__(self) -> None:
        self._deals: dict[str, dict[str, Any]] = {}
        self._fingerprints: dict[str, str] = {}
        self._decision_versions: dict[str, list[dict[str, Any]]] = {}
        self._watch_policies: dict[str, dict[str, Any]] = {}
        self._events: list[dict[str, Any]] = []

    # RC155 — Opportunity idempotency
    def build_fingerprint(
        self,
        *,
        source_id: str,
        external_offer_id: str,
        canonical_product_key: str,
        observed_at: str,
        price: float,
        currency: str,
    ) -> str:
        raw = "|".join(
            [
                source_id,
                external_offer_id,
                canonical_product_key,
                observed_at,
                str(float(price)),
                currency.upper(),
            ]
        )
        return sha256(raw.encode("utf-8")).hexdigest()

    def register_deal(
        self,
        *,
        source_id: str,
        external_offer_id: str,
        canonical_product_key: str,
        observed_at: str,
        price: float,
        currency: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fingerprint = self.build_fingerprint(
            source_id=source_id,
            external_offer_id=external_offer_id,
            canonical_product_key=canonical_product_key,
            observed_at=observed_at,
            price=price,
            currency=currency,
        )

        existing_id = self._fingerprints.get(fingerprint)

        if existing_id:
            return {
                "registered": False,
                "reason": "DUPLICATE_DEAL",
                "deal": deepcopy(self._deals[existing_id]),
            }

        deal_id = str(uuid4())
        deal = {
            "deal_id": deal_id,
            "fingerprint": fingerprint,
            "source_id": source_id,
            "external_offer_id": external_offer_id,
            "canonical_product_key": canonical_product_key,
            "observed_at": observed_at,
            "price": float(price),
            "currency": currency.upper(),
            "status": "DISCOVERED",
            "payload": payload or {},
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

        self._deals[deal_id] = deal
        self._fingerprints[fingerprint] = deal_id
        self._record_event(
            deal_id=deal_id,
            event_type="DEAL_REGISTERED",
            details={"status": "DISCOVERED"},
        )

        return {
            "registered": True,
            "reason": "DEAL_REGISTERED",
            "deal": deepcopy(deal),
            "metadata": {
                "idempotency_version": "deal_idempotency_v1"
            },
        }

    # RC156 — Decision versioning
    def append_decision_version(
        self,
        *,
        deal_id: str,
        decision: str,
        confidence: float,
        explanation: str,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if deal_id not in self._deals:
            return {
                "stored": False,
                "reason": "DEAL_NOT_FOUND",
                "version": None,
            }

        versions = self._decision_versions.setdefault(
            deal_id,
            [],
        )

        version = {
            "decision_version_id": str(uuid4()),
            "deal_id": deal_id,
            "version": len(versions) + 1,
            "decision": decision,
            "confidence": round(float(confidence), 2),
            "explanation": explanation,
            "evidence": evidence or {},
            "supersedes_version": (
                versions[-1]["version"]
                if versions
                else None
            ),
            "created_at": now_iso(),
        }

        versions.append(version)

        self._record_event(
            deal_id=deal_id,
            event_type="DECISION_VERSION_CREATED",
            details={
                "version": version["version"],
                "decision": decision,
            },
        )

        return {
            "stored": True,
            "reason": "DECISION_VERSION_STORED",
            "version": deepcopy(version),
            "metadata": {
                "versioning_version": "decision_versioning_v1"
            },
        }

    def get_decision_versions(
        self,
        deal_id: str,
    ) -> dict[str, Any]:
        versions = deepcopy(
            self._decision_versions.get(
                deal_id,
                [],
            )
        )

        return {
            "deal_id": deal_id,
            "version_count": len(versions),
            "versions": versions,
            "latest_version": (
                versions[-1]
                if versions
                else None
            ),
        }

    # RC157 — Watch policies
    def create_watch_policy(
        self,
        *,
        user_id: str,
        product_key: str,
        target_price: float | None = None,
        minimum_discount_pct: float = 0,
        minimum_confidence: float = 60,
        allowed_sources: list[str] | None = None,
    ) -> dict[str, Any]:
        policy_id = str(uuid4())

        policy = {
            "policy_id": policy_id,
            "user_id": user_id,
            "product_key": product_key,
            "target_price": target_price,
            "minimum_discount_pct": float(
                minimum_discount_pct
            ),
            "minimum_confidence": float(
                minimum_confidence
            ),
            "allowed_sources": allowed_sources or [],
            "active": True,
            "created_at": now_iso(),
        }

        self._watch_policies[policy_id] = policy

        return {
            "created": True,
            "policy": deepcopy(policy),
            "metadata": {
                "policy_version": "watch_policy_v1"
            },
        }

    def evaluate_watch_policies(
        self,
        *,
        user_id: str,
        opportunity: dict[str, Any],
    ) -> dict[str, Any]:
        matches = []

        for policy in self._watch_policies.values():
            if not policy["active"]:
                continue

            if policy["user_id"] != user_id:
                continue

            if policy["product_key"] != opportunity.get(
                "canonical_product_key"
            ):
                continue

            if (
                policy["allowed_sources"]
                and opportunity.get("source_id")
                not in policy["allowed_sources"]
            ):
                continue

            effective_price = float(
                opportunity.get(
                    "effective_price",
                    opportunity.get("price", 0),
                )
            )

            if (
                policy["target_price"] is not None
                and effective_price
                > float(policy["target_price"])
            ):
                continue

            if float(
                opportunity.get(
                    "observed_discount_pct",
                    0,
                )
            ) < policy["minimum_discount_pct"]:
                continue

            if float(
                opportunity.get(
                    "confidence_score",
                    0,
                )
            ) < policy["minimum_confidence"]:
                continue

            matches.append(
                {
                    "policy_id": policy["policy_id"],
                    "user_id": user_id,
                    "deal_id": opportunity.get("deal_id"),
                    "product_key": policy["product_key"],
                    "effective_price": effective_price,
                }
            )

        return {
            "match_count": len(matches),
            "matches": matches,
            "metadata": {
                "policy_version": "watch_policy_v1"
            },
        }

    # RC158 — Lifecycle transitions
    def transition_status(
        self,
        *,
        deal_id: str,
        new_status: str,
        reason: str,
        actor: str = "system",
    ) -> dict[str, Any]:
        deal = self._deals.get(deal_id)

        if deal is None:
            return {
                "transitioned": False,
                "reason": "DEAL_NOT_FOUND",
                "deal": None,
            }

        normalized = new_status.upper()

        if normalized not in self.VALID_STATUSES:
            return {
                "transitioned": False,
                "reason": "INVALID_STATUS",
                "deal": deepcopy(deal),
            }

        current = deal["status"]
        allowed = self.ALLOWED_TRANSITIONS[
            current
        ]

        if normalized not in allowed:
            return {
                "transitioned": False,
                "reason": "INVALID_STATUS_TRANSITION",
                "current_status": current,
                "requested_status": normalized,
                "deal": deepcopy(deal),
            }

        deal["status"] = normalized
        deal["updated_at"] = now_iso()

        self._record_event(
            deal_id=deal_id,
            event_type="DEAL_STATUS_CHANGED",
            details={
                "from_status": current,
                "to_status": normalized,
                "reason": reason,
                "actor": actor,
            },
        )

        return {
            "transitioned": True,
            "reason": "STATUS_TRANSITION_COMPLETED",
            "deal": deepcopy(deal),
            "metadata": {
                "lifecycle_version": "deal_lifecycle_v1"
            },
        }

    # RC159 — Operational queries/events
    def list_deals(
        self,
        *,
        status: str | None = None,
        product_key: str | None = None,
        source_id: str | None = None,
    ) -> dict[str, Any]:
        deals = list(self._deals.values())

        if status is not None:
            normalized = status.upper()
            deals = [
                item
                for item in deals
                if item["status"] == normalized
            ]

        if product_key is not None:
            deals = [
                item
                for item in deals
                if item["canonical_product_key"]
                == product_key
            ]

        if source_id is not None:
            deals = [
                item
                for item in deals
                if item["source_id"] == source_id
            ]

        return {
            "deal_count": len(deals),
            "deals": deepcopy(deals),
            "metadata": {
                "query_version": "deal_query_v1"
            },
        }

    def get_deal(
        self,
        deal_id: str,
    ) -> dict[str, Any] | None:
        deal = self._deals.get(deal_id)
        return deepcopy(deal) if deal else None

    def list_events(
        self,
        *,
        deal_id: str | None = None,
        event_type: str | None = None,
    ) -> dict[str, Any]:
        events = list(self._events)

        if deal_id is not None:
            events = [
                item
                for item in events
                if item["deal_id"] == deal_id
            ]

        if event_type is not None:
            events = [
                item
                for item in events
                if item["event_type"] == event_type
            ]

        return {
            "event_count": len(events),
            "events": deepcopy(events),
            "metadata": {
                "event_version": "deal_lifecycle_events_v1"
            },
        }

    def _record_event(
        self,
        *,
        deal_id: str,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        self._events.append(
            {
                "event_id": str(uuid4()),
                "deal_id": deal_id,
                "event_type": event_type,
                "details": deepcopy(details),
                "created_at": now_iso(),
            }
        )
