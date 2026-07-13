from app.domains.production_launch.service import ProductionLaunchService


def test_rc308_integrity_hash():
    s = ProductionLaunchService()
    r=s.calculate_integrity_hash(payload={"b":2,"a":1})
    assert len(r["hash"])==64