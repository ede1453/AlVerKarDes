import asyncio

from app.api.v1.recommendation_router import evaluate


def test_contract():
    result=asyncio.run(evaluate({"deal_score":95,"authenticity_score":96}))
    assert result["recommendation"]=="BUY_NOW"
    assert "confidence" in result
