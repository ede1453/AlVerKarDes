from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST_PATH = Path("release/release_manifest_v1.0.0.json")
EXPECTED_VERSION = "v1.0.0"
EXPECTED_PRODUCTION_PORT = 8000
EXPECTED_ALEMBIC_HEAD = "0014_deal_storage_sqlalchemy"
ALLOWED_READINESS_STATUSES = {"READY", "ACTION_REQUIRED"}
ALLOWED_CONNECTOR_MODES = {"mock", "fixture", "production"}
DIGEST_PATTERN = re.compile(r"^[a-f0-9]{64}$")
ENV_NAME_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


class ManifestValidationError(ValueError):
    pass


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _parse_generated_at(value: Any, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append("generated_at must be a non-empty ISO datetime string")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append("generated_at must be ISO-8601 parseable")


def _validate_connector_readiness(readiness: Any, errors: list[str]) -> None:
    if not isinstance(readiness, dict):
        errors.append("connector_readiness must be an object")
        return

    status = readiness.get("status")
    summary = readiness.get("summary")
    connectors = readiness.get("connectors")

    _require(status in ALLOWED_READINESS_STATUSES, "connector_readiness.status is invalid", errors)
    if not isinstance(summary, dict):
        errors.append("connector_readiness.summary must be an object")
        summary = {}
    if not isinstance(connectors, list):
        errors.append("connector_readiness.connectors must be a list")
        connectors = []

    expected_summary_keys = {
        "connector_count",
        "operational_ready_count",
        "production_ready_count",
        "mock_or_fixture_count",
        "action_required_count",
    }
    for key in expected_summary_keys:
        _require(isinstance(summary.get(key), int), f"summary.{key} must be an integer", errors)

    connector_ids: list[str] = []
    operational_ready_count = 0
    production_ready_count = 0
    mock_or_fixture_count = 0
    action_required_count = 0

    for index, item in enumerate(connectors):
        if not isinstance(item, dict):
            errors.append(f"connectors[{index}] must be an object")
            continue

        connector_id = item.get("connector_id")
        mode = item.get("mode")
        operational_ready = item.get("operational_ready")
        production_ready = item.get("production_ready")
        missing_required_env = item.get("missing_required_env")

        _require(isinstance(connector_id, str) and bool(connector_id), f"connectors[{index}].connector_id is required", errors)
        _require(mode in ALLOWED_CONNECTOR_MODES, f"connectors[{index}].mode is invalid", errors)
        _require(isinstance(operational_ready, bool), f"connectors[{index}].operational_ready must be boolean", errors)
        _require(isinstance(production_ready, bool), f"connectors[{index}].production_ready must be boolean", errors)
        _require(isinstance(missing_required_env, list), f"connectors[{index}].missing_required_env must be a list", errors)

        if isinstance(connector_id, str):
            connector_ids.append(connector_id)
        if operational_ready is True:
            operational_ready_count += 1
        if production_ready is True:
            production_ready_count += 1
        if mode in {"mock", "fixture"}:
            mock_or_fixture_count += 1
        if isinstance(missing_required_env, list):
            if missing_required_env:
                action_required_count += 1
            for env_name in missing_required_env:
                _require(
                    isinstance(env_name, str) and bool(ENV_NAME_PATTERN.fullmatch(env_name)),
                    f"connectors[{index}].missing_required_env contains an invalid env name",
                    errors,
                )

    _require(len(connector_ids) == len(set(connector_ids)), "connector ids must be unique", errors)
    _require(summary.get("connector_count") == len(connectors), "summary.connector_count does not match connectors length", errors)
    _require(summary.get("operational_ready_count") == operational_ready_count, "summary.operational_ready_count is inconsistent", errors)
    _require(summary.get("production_ready_count") == production_ready_count, "summary.production_ready_count is inconsistent", errors)
    _require(summary.get("mock_or_fixture_count") == mock_or_fixture_count, "summary.mock_or_fixture_count is inconsistent", errors)
    _require(summary.get("action_required_count") == action_required_count, "summary.action_required_count is inconsistent", errors)


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    _require(manifest.get("version") == EXPECTED_VERSION, "version must be v1.0.0", errors)
    _require(isinstance(manifest.get("commit_sha"), str) and bool(manifest.get("commit_sha")), "commit_sha is required", errors)
    _require(
        isinstance(manifest.get("source_digest_sha256"), str)
        and bool(DIGEST_PATTERN.fullmatch(manifest.get("source_digest_sha256", ""))),
        "source_digest_sha256 must be a 64 character lowercase sha256 hex digest",
        errors,
    )
    _parse_generated_at(manifest.get("generated_at"), errors)
    _require(manifest.get("release_status") == "RELEASE_CANDIDATE_APPROVED", "release_status is invalid", errors)
    _require(manifest.get("production_port") == EXPECTED_PRODUCTION_PORT, "production_port must be 8000", errors)
    _require(manifest.get("alembic_head") == EXPECTED_ALEMBIC_HEAD, "alembic_head is invalid", errors)
    _validate_connector_readiness(manifest.get("connector_readiness"), errors)

    return errors


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    path = Path(args[0]) if args else DEFAULT_MANIFEST_PATH

    if not path.exists():
        print(f"Release manifest validation failed: {path} does not exist")
        return 1

    try:
        manifest = load_manifest(path)
    except json.JSONDecodeError as exc:
        print(f"Release manifest validation failed: invalid JSON: {exc}")
        return 1

    errors = validate_manifest(manifest)
    if errors:
        print("Release manifest validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Release manifest validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
