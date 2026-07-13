from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc282_segment_membership():
    s = GrowthRevenueIntelligenceService()
    s.create_user_segment(segment_id="seg1",name="Power",rules={"purchase_count":{"min":5}})
    assert s.evaluate_segment_membership(segment_id="seg1",user_features={"purchase_count":7})["member"] is True