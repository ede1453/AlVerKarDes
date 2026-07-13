from pathlib import Path


def test_rc2_auto_merge_scripts_exist():
    expected = [
        "scripts/apply_demo_macbook_merge.ps1",
        "scripts/rc2_demo_full_flow.ps1",
    ]

    missing = [item for item in expected if not Path(item).exists()]
    assert missing == []


def test_apply_demo_macbook_merge_uses_merge_endpoints():
    content = Path("scripts/apply_demo_macbook_merge.ps1").read_text(encoding="utf-8")

    assert "/api/v1/products/merge/apply" in content
    assert "/api/v1/products/merge/verify" in content
    assert "/api/v1/system/release-health" in content


def test_rc2_demo_full_flow_runs_seed_merge_inspect():
    content = Path("scripts/rc2_demo_full_flow.ps1").read_text(encoding="utf-8")

    assert "seed_demo_connectors.ps1" in content
    assert "apply_demo_macbook_merge.ps1" in content
    assert "inspect_prod_data.ps1" in content
