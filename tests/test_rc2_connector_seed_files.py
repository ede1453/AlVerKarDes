from pathlib import Path


def test_rc2_connector_seed_scripts_exist():
    expected = [
        "scripts/seed_demo_connectors.ps1",
        "scripts/inspect_prod_data.ps1",
    ]

    missing = [item for item in expected if not Path(item).exists()]
    assert missing == []


def test_seed_demo_connectors_hits_ingest_endpoint():
    content = Path("scripts/seed_demo_connectors.ps1").read_text(encoding="utf-8")

    assert "/api/v1/connectors/ingest" in content
    assert "Example Laptop" in content


def test_inspect_prod_data_queries_core_tables():
    content = Path("scripts/inspect_prod_data.ps1").read_text(encoding="utf-8")

    assert "products" in content
    assert "offers" in content
    assert "prices" in content
