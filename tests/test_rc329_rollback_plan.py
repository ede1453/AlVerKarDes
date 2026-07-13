from app.domains.production_launch.service import ProductionLaunchService


def test_rc329_rollback_plan():
    s = ProductionLaunchService()
    r=s.create_rollback_plan(deployment_id="d1",previous_image_tag="aici:0.9",migration_reversible=True)
    assert r["plan"]["executable"] is True