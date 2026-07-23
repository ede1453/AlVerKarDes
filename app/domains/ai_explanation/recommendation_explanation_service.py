from __future__ import annotations

from copy import deepcopy
from typing import Any


class RecommendationExplanationService:
    def explain(
        self,
        *,
        recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        decision = recommendation.get(
            "decision",
            "INSUFFICIENT_DATA",
        )
        evidence = recommendation.get(
            "evidence",
            {},
        )

        reasons: list[str] = []

        discount = evidence.get(
            "observed_discount_pct"
        )
        if discount is not None:
            reasons.append(
                f"OBSERVED_DISCOUNT_{discount}"
            )

        source_confidence = evidence.get(
            "source_confidence"
        )
        if source_confidence is not None:
            reasons.append(
                f"SOURCE_CONFIDENCE_{source_confidence}"
            )

        freshness = evidence.get(
            "freshness_status"
        )
        if freshness:
            reasons.append(
                f"FRESHNESS_{freshness}"
            )

        if evidence.get(
            "anomaly_detected",
            False,
        ):
            reasons.append(
                "PRICE_ANOMALY_DETECTED"
            )

        summaries = {
            "BUY": "Fiyat, kaynak güveni ve veri tazeliği satın alma kararını destekliyor.",
            "WAIT": "Fırsat mevcut ancak daha güçlü doğrulama veya daha iyi fiyat beklenmeli.",
            "DO_NOT_BUY": "Risk veya yanıltıcı fiyat sinyali nedeniyle satın alma önerilmiyor.",
            "INSUFFICIENT_DATA": "Güvenilir karar için yeterli veri bulunmuyor.",
        }

        return {
            "decision": decision,
            "summary": summaries.get(
                decision,
                "Karar açıklaması oluşturuldu.",
            ),
            "reasons": reasons,
            "evidence": deepcopy(evidence),
            "metadata": {
                "explanation_version": "recommendation_explanation_v1"
            },
        }
