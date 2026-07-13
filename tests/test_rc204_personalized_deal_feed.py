from app.domains.deal_feed.service import DealFeedBuilder


def test_rc204_feed_sorted_by_personalized_score():
    result = DealFeedBuilder().build(
        deals=[
            {
                "deal_id":"d1",
                "confidence_score":80,
                "opportunity_score":70,
                "brand":"apple",
                "category":"laptop",
                "source_id":"amazon",
                "effective_price":900,
                "observed_discount_pct":20,
            },
            {
                "deal_id":"d2",
                "confidence_score":85,
                "opportunity_score":85,
                "brand":"lenovo",
                "category":"laptop",
                "source_id":"amazon",
                "effective_price":850,
                "observed_discount_pct":25,
            },
        ],
        preferences={
            "preferred_brands":["apple"]
        },
        minimum_confidence=70,
    )
    assert result["feed_count"] == 2
    assert result["items"][0]["deal_id"] in {"d1", "d2"}
    assert result["items"][0]["personalized_score"] >= result["items"][1]["personalized_score"]
