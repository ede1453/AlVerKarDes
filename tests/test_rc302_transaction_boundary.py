from app.domains.production_launch.service import ProductionLaunchService


def test_rc302_transaction_boundary():
    s = ProductionLaunchService()
    r=s.validate_transaction_boundary(writes=[{"id":1}],committed=False,rollback_requested=True)
    assert r["rolled_back_count"]==1