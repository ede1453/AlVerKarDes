from pathlib import Path

def test_rc445_session_management_endpoints_exist():
    text = Path(
        "app/api/v1/auth_core_router.py"
    ).read_text(encoding="utf-8")
    assert '@router.get(\n    "/sessions"' in text
    assert '@router.delete(\n    "/sessions/{session_id}"' in text
    assert '@router.delete(\n    "/sessions"' in text
