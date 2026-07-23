from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers


def test_deal_detection_vertical_slice_from_realistic_agent_style_input():
    # VISION-002 (ADR-019): this used to call ai_shopping_agent's /run to
    # build a realistic price_history/top_offer/personalization payload
    # before feeding it to deal_detection -- ai_shopping_agent was archived
    # (no production caller), but its actual real output shape for this
    # exact scenario was captured before archiving and is reproduced
    # directly here, so deal_detection's own vertical slice coverage (same
    # scenario, same expected deal_score) is unchanged.
    with TestClient(app) as client:
        headers = auth_headers(client)

        deal_response = client.post(
            "/api/v1/deal-detection/detect",
            headers=headers,
            json={
                "product_key": "apple::macbook-air::m3::de",
                "offer": {"marketplace": "saturn", "price": "949.00"},
                "price_history": {
                    "product_key": "apple::macbook-air::m3::de",
                    "currency": "EUR",
                    "point_count": 2,
                    "min_price": "949.00",
                    "max_price": "999.00",
                    "average_price": "974.00",
                    "latest_price": "999.00",
                    "trend": "UP",
                },
                "personalization": {
                    "top_offer": {"personalization_score": 95},
                },
            },
        )

    assert deal_response.status_code == 200
    assert deal_response.json()["deal_score"] >= 70
