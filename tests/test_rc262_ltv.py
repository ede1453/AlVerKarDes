from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc262_ltv():
    s = GrowthRevenueIntelligenceService()
    r=s.calculate_lifetime_value(average_order_value=100,purchase_frequency_per_year=4,gross_margin_pct=20,retention_years=3)
    assert r["ltv"]==240