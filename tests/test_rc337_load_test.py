from app.domains.production_launch.service import ProductionLaunchService


def test_rc337_load_test():
    s = ProductionLaunchService()
    r=s.evaluate_load_test(requests_per_second=100,error_rate=0.01,p95_latency_ms=200,minimum_rps=50,maximum_error_rate=0.05,maximum_p95_latency_ms=500)
    assert r["passed"] is True