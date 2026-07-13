from app.domains.production_launch.service import ProductionLaunchService


def test_rc339_go_no_go():
    s = ProductionLaunchService()
    s.register_release_check(check_name="security",passed=True)
    s.record_smoke_test(test_name="health",passed=True)
    s.evaluate_load_test(requests_per_second=100,error_rate=0.01,p95_latency_ms=200,minimum_rps=50,maximum_error_rate=0.05,maximum_p95_latency_ms=500)
    r=s.evaluate_go_no_go(required_checks=["security"])
    assert r["decision"]=="GO"