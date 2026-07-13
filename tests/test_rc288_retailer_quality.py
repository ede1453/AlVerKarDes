from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc288_retailer_quality():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_retailer_quality(offer_count=100,valid_offer_count=90,false_positive_count=1)["retailer_quality_score"]==85.0
