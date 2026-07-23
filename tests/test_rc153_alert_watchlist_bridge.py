from app.domains.deal_operations.service import DealAlertBridge
from app.domains.watchlist.watchlist_matcher import WatchlistMatcher


def test_rc153_alert_bridge():
    result = DealAlertBridge().build_alert(
        user_id="user-1",
        opportunity={
            "opportunity_id":"opp-1",
            "canonical_product_key":"product-1",
        },
        recommendation={
            "decision":"BUY",
            "confidence":85,
            "summary":"Strong deal",
            "truth_status":"GENUINE_STRONG_DISCOUNT",
        },
    )
    assert result["should_alert"] is True
    assert result["alert_level"] == "URGENT"

def test_rc153_watchlist_matcher():
    result = WatchlistMatcher().match(
        watch_items=[{
            "watch_id":"watch-1",
            "user_id":"user-1",
            "product_key":"product-1",
            "target_price":900,
            "minimum_confidence":70,
            "active":True,
        }],
        opportunity={
            "canonical_product_key":"product-1",
            "effective_price":850,
        },
        recommendation={
            "confidence":85,
        },
    )
    assert result["match_count"] == 1
