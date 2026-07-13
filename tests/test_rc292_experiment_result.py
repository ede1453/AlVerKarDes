from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc292_experiment_result():
    s = GrowthRevenueIntelligenceService()
    s.create_growth_experiment(experiment_id="e1",variants=["A","B"],target_metric="conversion")
    assert s.record_experiment_result(experiment_id="e1",variant="A",metric_value=1)["recorded"] is True