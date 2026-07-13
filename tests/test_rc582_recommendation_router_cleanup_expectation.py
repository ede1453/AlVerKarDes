from pathlib import Path


def test_rc582_router_no_longer_includes_legacy_recommendation_router():
    content = Path("app/api/v1/router.py").read_text(encoding="utf-8")

    assert "from app.domains.recommendations.router import router as legacy_recommendations_router" not in content
    assert "api_router.include_router(legacy_recommendations_router" not in content


def test_rc582_router_keeps_api_v1_recommendations_router():
    content = Path("app/api/v1/router.py").read_text(encoding="utf-8")

    assert "from app.api.v1.recommendations_router import router as recommendations_router" in content
    assert "api_router.include_router(recommendations_router)" in content
