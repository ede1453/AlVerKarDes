from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc291_experiment_create():
    s = GrowthRevenueIntelligenceService()
    assert s.create_growth_experiment(experiment_id="e1",variants=["A","B"],target_metric="conversion")["created"] is True
