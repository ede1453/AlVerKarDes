from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc281_segment_create():
    s = GrowthRevenueIntelligenceService()
    assert s.create_user_segment(segment_id="seg1",name="Power",rules={"purchase_count":{"min":5}})["created"] is True
