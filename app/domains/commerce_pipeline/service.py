from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.domains.commerce_ingestion.marketplace_connectors import (
    MarketplaceConnectorFactory,
)
from app.domains.commerce_ingestion.price_quality import (
    PriceQualityPipeline,
)
from app.domains.deal_intelligence.service import (
    DealIntelligenceService,
)
from app.domains.deal_operations.service import (
    DealDecisionOperationsService,
)
from app.domains.deal_persistence.service import (
    DealPersistenceService,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CommercePipelineService:
    def __init__(self) -> None:
        self.price_quality = PriceQualityPipeline()
        self.deal_intelligence = DealIntelligenceService()
        self.deal_operations = DealDecisionOperationsService()
        self.persistence = DealPersistenceService()
        self._runs: dict[str, dict[str, Any]] = {}

    # RC196 — Marketplace normalization stage
    def normalize_marketplace_items(
        self,
        *,
        marketplace: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        connector = MarketplaceConnectorFactory.create(
            marketplace
        )

        normalized = []

        for item in items:
            connector_result = connector.normalize(item)

            # Connector yalnızca ortak marketplace alanlarını normalize eder.
            # Pipeline bağlamındaki fiyat geçmişi ve güven alanları korunur.
            normalized.append(
                {
                    **item,
                    **connector_result,
                }
            )

        return {
            "normalized_count": len(normalized),
            "items": normalized,
            "metadata": {
                "stage": "marketplace_normalization",
                "version": "commerce_pipeline_v1",
            },
        }

    # RC197 — Quality enrichment stage
    def enrich_price_quality(
        self,
        *,
        offers: list[dict[str, Any]],
        target_currency: str,
        exchange_rates: dict[str, float],
        reference_time: str | None = None,
    ) -> dict[str, Any]:
        prepared = []

        for offer in offers:
            prepared.append(
                {
                    **offer,
                    "source_id": (
                        offer.get("source_id")
                        or offer.get("marketplace")
                        or "unknown"
                    ),
                    "observed_at": (
                        offer.get("observed_at")
                        or now_iso()
                    ),
                    "historical_prices": offer.get(
                        "historical_prices",
                        [],
                    ),
                    "source_trust_score": int(
                        offer.get(
                            "source_trust_score",
                            50,
                        )
                    ),
                    "verified_source": bool(
                        offer.get(
                            "verified_source",
                            False,
                        )
                    ),
                    "shipping_cost": float(
                        offer.get(
                            "shipping_cost",
                            0,
                        )
                    ),
                }
            )

        return self.price_quality.evaluate_offers(
            offers=prepared,
            target_currency=target_currency,
            exchange_rates=exchange_rates,
            reference_time=reference_time,
        )

    # RC198 — Deal decision stage
    def evaluate_deals(
        self,
        *,
        quality_result: dict[str, Any],
    ) -> dict[str, Any]:
        opportunities = []

        for offer in quality_result.get(
            "offers",
            [],
        ):
            normalized_price = (
                offer.get("normalized_price")
                or offer.get("price")
            )

            opportunities.append(
    {
        **offer,

        "price": float(normalized_price),

        "effective_price": (
            float(normalized_price)
            + float(
                offer.get(
                    "shipping_cost",
                    0,
                )
            )
        ),

        "historical_prices": offer.get(
            "historical_prices",
            [],
        ),

        "claimed_original_price": offer.get(
            "claimed_original_price"
        ),

        "discount_percent": offer.get(
            "discount_percent"
        ),

        "marketplace": offer.get(
            "marketplace"
        ),

        "verified_source": offer.get(
            "verified_source",
            False,
        ),

        "canonical_product_key": offer.get(
            "canonical_product_key"
        ),

        "source_confidence": int(
            offer.get(
                "source_confidence",
                offer.get(
                    "source_trust_score",
                    0,
                ),
            )
        ),

        "freshness_status": offer.get(
            "freshness_status",
            "STALE",
        ),

        "anomaly_detected": bool(
            offer.get(
                "anomalous",
                False,
            )
        ),

        "review_reliability": int(
            offer.get(
                "review_reliability",
                50,
            )
        ),
    }
)

        return self.deal_intelligence.evaluate(
            opportunities=opportunities
        )

    # RC199 — Persistence and operational stage
    def persist_best_deal(
        self,
        *,
        intelligence_result: dict[str, Any],
        user_id: str | None = None,
    ) -> dict[str, Any]:
        ranking = intelligence_result.get(
            "ranking",
            {},
        )
        opportunities = ranking.get(
            "opportunities",
            [],
        )

        operations_result = (
            self.deal_operations.evaluate_and_store(
                opportunities=opportunities,
                user_id=user_id,
            )
            if opportunities
            else {
                "stored_count": 0,
                "opportunities": [],
                "best_opportunity": None,
                "recommendation": None,
                "explanation": None,
                "decision_record": None,
                "alert": None,
                "watchlist_matches": {
                    "match_count": 0,
                    "matches": [],
                },
            }
        )

        best = operations_result.get(
            "best_opportunity"
        )

        persistence_result = None

        if best:
            deal_id = best.get(
                "opportunity_id"
            ) or str(uuid4())

            persistence_result = (
                self.persistence.persist_deal(
                    deal_id=deal_id,
                    payload={
                        "opportunity": deepcopy(best),
                        "recommendation": deepcopy(
                            operations_result.get(
                                "recommendation"
                            )
                        ),
                        "explanation": deepcopy(
                            operations_result.get(
                                "explanation"
                            )
                        ),
                        "alert": deepcopy(
                            operations_result.get(
                                "alert"
                            )
                        ),
                    },
                )
            )

        return {
            "operations": operations_result,
            "persistence": persistence_result,
        }

    # RC200 — End-to-end orchestrator
    def run_pipeline(
        self,
        *,
        marketplace: str,
        items: list[dict[str, Any]],
        target_currency: str,
        exchange_rates: dict[str, float],
        reference_time: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        run_id = str(uuid4())
        started_at = now_iso()

        normalized = self.normalize_marketplace_items(
            marketplace=marketplace,
            items=items,
        )

        quality = self.enrich_price_quality(
            offers=normalized["items"],
            target_currency=target_currency,
            exchange_rates=exchange_rates,
            reference_time=reference_time,
        )

        intelligence = self.evaluate_deals(
            quality_result=quality
        )

        stored = self.persist_best_deal(
            intelligence_result=intelligence,
            user_id=user_id,
        )

        status = (
            "COMPLETED"
            if stored["persistence"] is not None
            else "COMPLETED_WITHOUT_PERSISTENCE"
        )

        run = {
            "run_id": run_id,
            "status": status,
            "marketplace": marketplace,
            "input_count": len(items),
            "normalized_count": normalized[
                "normalized_count"
            ],
            "quality_evaluated_count": quality.get(
                "evaluated_count",
                0,
            ),
            "recommendation": intelligence.get(
                "recommendation"
            ),
            "best_opportunity": intelligence.get(
                "ranking",
                {},
            ).get("best_opportunity"),
            "persistence": stored["persistence"],
            "alert": stored["operations"].get(
                "alert"
            ),
            "started_at": started_at,
            "completed_at": now_iso(),
            "metadata": {
                "pipeline_version": "commerce_pipeline_v1"
            },
        }

        self._runs[run_id] = run

        return {
            "executed": True,
            "run": deepcopy(run),
            "stages": {
                "normalization": normalized,
                "price_quality": quality,
                "deal_intelligence": intelligence,
                "deal_operations": stored["operations"],
            },
        }

    def get_run(
        self,
        run_id: str,
    ) -> dict[str, Any] | None:
        run = self._runs.get(run_id)
        return deepcopy(run) if run else None

    def list_runs(self) -> dict[str, Any]:
        runs = deepcopy(
            list(self._runs.values())
        )
        return {
            "run_count": len(runs),
            "runs": runs,
        }
