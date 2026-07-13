from app.domains.production_launch.service import ProductionLaunchService


def test_rc326_container_image():
    s = ProductionLaunchService()
    assert s.evaluate_container_image(image_tag="aici:1.0",digest="sha256:abc",non_root_user=True,healthcheck_present=True)["valid"] is True
