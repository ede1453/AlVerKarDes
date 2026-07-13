from pathlib import Path

from app.main import app
from scripts.api_contract_snapshot import (
    assert_no_breaking_changes,
    extract_contract,
    save_contract_snapshot,
)

_RUNTIME_TMP = Path(__file__).resolve().parent / "runtime_tmp"


def _runtime_file(name: str) -> Path:
    _RUNTIME_TMP.mkdir(exist_ok=True)
    path = _RUNTIME_TMP / name
    if path.exists():
        path.unlink()
    return path


def test_current_api_contract_snapshot_can_be_saved_and_compared():
    snapshot_path = _runtime_file("openapi_snapshot_v1.json")

    saved = save_contract_snapshot(app.openapi(), snapshot_path)
    loaded_text = snapshot_path.read_text(encoding="utf-8")

    assert saved["path_count"] > 0
    assert "paths" in loaded_text

    current = extract_contract(app.openapi())
    comparison = assert_no_breaking_changes(previous=saved, current=current)

    assert comparison["breaking_change_count"] == 0


def test_current_api_contract_contains_recent_llm_endpoints():
    contract = extract_contract(app.openapi())
    paths = contract["paths"]

    assert "/api/v1/llm-streaming/preview" in paths
    assert "/api/v1/llm-orchestration/run-intelligent" in paths
    assert "/api/v1/llm-provider-health/summary" in paths