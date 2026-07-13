from app.domains.user_value.service import UserValueIntelligenceService


def test_rc249_watch_entry():
    r=UserValueIntelligenceService().create_watch_entry(user_id="u1",product_key="p1",target_price=700)
    assert r["created"] is True
