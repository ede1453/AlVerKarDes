from app.domains.production_launch.service import ProductionLaunchService


def test_rc340_release_manifest():
    s = ProductionLaunchService()
    r=s.build_release_manifest(version="v1.0.0",commit_sha="abc123",image_digest="sha256:def",go_no_go_decision="GO")
    assert r["manifest"]["publishable"] is True