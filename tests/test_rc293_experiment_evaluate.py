from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc293_experiment_evaluate():
    s = GrowthRevenueIntelligenceService()
    s.create_growth_experiment(experiment_id="e1",variants=["A","B"],target_metric="conversion")
    s.record_experiment_result(experiment_id="e1",variant="A",metric_value=2)
    s.record_experiment_result(experiment_id="e1",variant="B",metric_value=1)
    assert s.evaluate_experiment(experiment_id="e1")["winner"]=="A"