from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class CommerceIngestionService:
    ALLOWED_SOURCE_TYPES = {"manual", "csv", "json", "api", "affiliate_feed"}

    def __init__(self) -> None:
        self._sources = {}
        self._raw_offers = {}
        self._snapshots = {}
        self._fingerprints = set()
        self._runs = {}

    def register_source(self, source_id: str, name: str, source_type: str,
                        country: str, currency: str, enabled: bool = True,
                        trust_score: int = 50, metadata: dict | None = None) -> dict:
        source_type = source_type.lower()
        if source_type not in self.ALLOWED_SOURCE_TYPES:
            return {"registered": False, "reason": "UNSUPPORTED_SOURCE_TYPE", "source": None}
        if not 0 <= trust_score <= 100:
            return {"registered": False, "reason": "INVALID_TRUST_SCORE", "source": None}
        source = {
            "source_id": source_id, "name": name, "source_type": source_type,
            "country": country.upper(), "currency": currency.upper(),
            "enabled": enabled, "trust_score": trust_score,
            "metadata": metadata or {}, "registered_at": now_iso(),
        }
        self._sources[source_id] = source
        return {"registered": True, "reason": "SOURCE_REGISTERED",
                "source": deepcopy(source),
                "metadata": {"registry_version": "connector_source_registry_v1"}}

    def list_sources(self, enabled: bool | None = None,
                     country: str | None = None) -> dict:
        items = list(self._sources.values())
        if enabled is not None:
            items = [x for x in items if x["enabled"] is enabled]
        if country is not None:
            items = [x for x in items if x["country"] == country.upper()]
        return {"source_count": len(items), "sources": deepcopy(items),
                "metadata": {"registry_version": "connector_source_registry_v1"}}

    def collect_raw_offer(self, source_id: str, external_offer_id: str,
                          product_title: str, product_url: str, price: float,
                          currency: str, availability: str = "unknown",
                          seller_name: str | None = None,
                          observed_at: str | None = None,
                          raw_payload: dict | None = None) -> dict:
        source = self._sources.get(source_id)
        if source is None:
            return {"collected": False, "reason": "SOURCE_NOT_FOUND", "raw_offer": None}
        if not source["enabled"]:
            return {"collected": False, "reason": "SOURCE_DISABLED", "raw_offer": None}
        if price <= 0:
            return {"collected": False, "reason": "INVALID_PRICE", "raw_offer": None}
        rid = str(uuid4())
        item = {
            "raw_offer_id": rid, "source_id": source_id,
            "external_offer_id": external_offer_id,
            "product_title": product_title.strip(),
            "product_url": product_url.strip(), "price": float(price),
            "currency": currency.upper(), "availability": availability.lower(),
            "seller_name": seller_name, "observed_at": observed_at or now_iso(),
            "raw_payload": raw_payload or {}, "collected_at": now_iso(),
        }
        self._raw_offers[rid] = item
        return {"collected": True, "reason": "RAW_OFFER_COLLECTED",
                "raw_offer": deepcopy(item),
                "metadata": {"collection_version": "raw_offer_collection_v1"}}

    def normalize_raw_offer(self, raw_offer_id: str,
                            canonical_product_key: str | None = None) -> dict:
        raw = self._raw_offers.get(raw_offer_id)
        if raw is None:
            return {"normalized": False, "reason": "RAW_OFFER_NOT_FOUND", "offer": None}
        title = " ".join(raw["product_title"].replace("_", " ").replace("-", " ").split())
        key = canonical_product_key or title.lower().replace(" ", "-")
        offer = {
            "offer_id": raw_offer_id, "source_id": raw["source_id"],
            "external_offer_id": raw["external_offer_id"],
            "canonical_product_key": key, "normalized_title": title,
            "product_url": raw["product_url"], "price": raw["price"],
            "currency": raw["currency"], "availability": raw["availability"],
            "seller_name": raw["seller_name"], "observed_at": raw["observed_at"],
            "normalization_confidence": 100 if canonical_product_key else 60,
        }
        return {"normalized": True, "reason": "RAW_OFFER_NORMALIZED",
                "offer": offer,
                "metadata": {"normalization_version": "offer_normalization_v1"}}

    def ingest_price_snapshot(self, offer: dict[str, Any]) -> dict:
        required = {"source_id", "external_offer_id", "canonical_product_key",
                    "price", "currency", "observed_at"}
        missing = sorted(x for x in required if x not in offer)
        if missing:
            return {"ingested": False, "reason": "MISSING_REQUIRED_FIELDS",
                    "missing_fields": missing, "snapshot": None}
        raw = "|".join(str(offer[x]) for x in
                       ["source_id", "external_offer_id", "price", "currency", "observed_at"])
        fingerprint = sha256(raw.encode()).hexdigest()
        if fingerprint in self._fingerprints:
            return {"ingested": False, "reason": "DUPLICATE_PRICE_SNAPSHOT",
                    "snapshot": None, "fingerprint": fingerprint}
        sid = str(uuid4())
        snapshot = {
            "snapshot_id": sid, "fingerprint": fingerprint,
            "source_id": offer["source_id"],
            "external_offer_id": offer["external_offer_id"],
            "canonical_product_key": offer["canonical_product_key"],
            "price": float(offer["price"]),
            "currency": str(offer["currency"]).upper(),
            "availability": offer.get("availability", "unknown"),
            "observed_at": offer["observed_at"], "ingested_at": now_iso(),
        }
        self._fingerprints.add(fingerprint)
        self._snapshots[sid] = snapshot
        return {"ingested": True, "reason": "PRICE_SNAPSHOT_INGESTED",
                "snapshot": deepcopy(snapshot),
                "metadata": {"ingestion_version": "price_snapshot_ingestion_v1"}}

    def start_connector_run(self, source_id: str) -> dict:
        if source_id not in self._sources:
            return {"started": False, "reason": "SOURCE_NOT_FOUND", "run": None}
        rid = str(uuid4())
        run = {"run_id": rid, "source_id": source_id, "status": "RUNNING",
               "started_at": now_iso(), "completed_at": None,
               "collected_count": 0, "ingested_count": 0,
               "failed_count": 0, "error": None}
        self._runs[rid] = run
        return {"started": True, "reason": "CONNECTOR_RUN_STARTED",
                "run": deepcopy(run),
                "metadata": {"health_version": "connector_run_health_v1"}}

    def complete_connector_run(self, run_id: str, collected_count: int,
                               ingested_count: int, failed_count: int = 0,
                               error: str | None = None) -> dict:
        run = self._runs.get(run_id)
        if run is None:
            return {"completed": False, "reason": "RUN_NOT_FOUND", "run": None}
        run.update({
            "status": "FAILED" if error else "COMPLETED",
            "completed_at": now_iso(), "collected_count": collected_count,
            "ingested_count": ingested_count, "failed_count": failed_count,
            "error": error,
        })
        return {"completed": True, "reason": "CONNECTOR_RUN_COMPLETED",
                "run": deepcopy(run),
                "metadata": {"health_version": "connector_run_health_v1"}}

    def get_connector_health(self, source_id: str) -> dict:
        source = self._sources.get(source_id)
        if source is None:
            return {"healthy": False, "reason": "SOURCE_NOT_FOUND",
                    "source_id": source_id, "latest_run": None}
        runs = [x for x in self._runs.values() if x["source_id"] == source_id]
        latest = sorted(runs, key=lambda x: x["started_at"])[-1] if runs else None
        if not source["enabled"]:
            status, healthy = "DISABLED", False
        elif latest is None:
            status, healthy = "UNKNOWN", False
        elif latest["status"] == "COMPLETED":
            status, healthy = "HEALTHY", True
        else:
            status, healthy = "UNHEALTHY", False
        return {"healthy": healthy, "status": status,
                "source_id": source_id, "source_name": source["name"],
                "latest_run": deepcopy(latest),
                "metadata": {"health_version": "connector_run_health_v1"}}
