from pathlib import Path


def test_rc340_health_wait_checks_container_state_and_logs():
    text = Path(
        "scripts/wait_for_production_api.ps1"
    ).read_text(encoding="utf-8")

    assert ".State.Health.Status" in text
    assert "logs --no-color --tail=200 api" in text
    assert 'state -eq "exited"' in text
