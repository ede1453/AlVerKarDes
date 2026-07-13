from pathlib import Path


def test_rc340_environment_example_uses_runtime_setting_name():
    text = Path(
        "config/production.env.example"
    ).read_text(encoding="utf-8")

    assert "JWT_SECRET=" in text
    assert (
        "JWT_SECRET_KEY="
        not in "\n".join(
            line
            for line in text.splitlines()
            if not line.strip().startswith("#")
        )
    )
