from pathlib import Path


def test_rc58_router_import_aliases_are_unique():
    router_file = Path("app/api/v1/router.py")
    content = router_file.read_text(encoding="utf-8")

    aliases = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("from ") and " import router as " in line:
            aliases.append(line.rsplit(" import router as ", 1)[1].strip())

    duplicates = sorted({alias for alias in aliases if aliases.count(alias) > 1})

    assert duplicates == []


def test_rc58_recommendation_router_uses_only_api_v1_compat_router():
    content = Path("app/api/v1/router.py").read_text(encoding="utf-8")

    assert "legacy_recommendations_router" not in content
    assert "from app.domains.recommendations.router import router as legacy_recommendations_router" not in content
    assert "api_router.include_router(legacy_recommendations_router" not in content

    assert "recommendations_router" in content
    assert "from app.api.v1.recommendations_router import router as recommendations_router" in content
    assert "api_router.include_router(recommendations_router)" in content