from app.domains.ai_explanation.explanation_service import AIExplanationService
from app.domains.events.event_repository_factory import reset_event_repository


def test_ai_explanation_service_emits_event():
    reset_event_repository()
    service = AIExplanationService()

    result = service.explain(
        {
            "agent_decision": {"decision": "BUY_NOW"},
            "deal_detection": {"deal_level": "EXCELLENT_DEAL"},
            "discount_intelligence": {"discount_quality": "EXCELLENT_REAL_DISCOUNT", "fake_discount_risk": "LOW"},
            "smart_alert": {"alert_level": "URGENT"},
            "price_prediction": {"recommendation_hint": "BUY_SOON"},
        }
    )

    assert result["headline"] == "This looks like a strong buy opportunity"
    assert result["metadata"]["prompt"]["prompt_version"] == "shopping_explanation_v1"

    events = service.event_bus_service.list_recent({"event_type": "ai_explanation.generated", "source": "ai_explanation"})
    assert events


def test_ai_explanation_service_cache_hit_on_second_call():
    service = AIExplanationService()
    payload = {
        "agent_decision": {"decision": "BUY_NOW"},
        "ttl_seconds": 300,
    }

    first = service.explain_cached(payload)
    second = service.explain_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
