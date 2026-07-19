from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ConnectorReadinessSpec:
    connector_id: str
    display_name: str
    mode_env: str | None
    default_mode: str
    required_env: tuple[str, ...] = ()
    optional_env: tuple[str, ...] = ()
    mock_safe: bool = True


def _env_is_enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _present(env: Mapping[str, str], key: str) -> bool:
    return bool(str(env.get(key, "")).strip())


def _mode(spec: ConnectorReadinessSpec, env: Mapping[str, str]) -> str:
    if spec.mode_env is None:
        return spec.default_mode
    if _env_is_enabled(env.get(spec.mode_env)):
        return "fixture"
    return spec.default_mode


def build_connector_readiness(env: Mapping[str, str] | None = None) -> dict:
    values = os.environ if env is None else env
    specs = [
        ConnectorReadinessSpec(
            connector_id="mock_marketplace",
            display_name="Mock Marketplace",
            mode_env=None,
            default_mode="mock",
        ),
        ConnectorReadinessSpec(
            connector_id="amazon_creators",
            display_name="Amazon Creators",
            mode_env="AMAZON_CREATORS_FIXTURE_MODE",
            default_mode="production",
            required_env=(
                "AMAZON_CREATORS_CLIENT_ID",
                "AMAZON_CREATORS_CLIENT_SECRET",
                "AMAZON_CREATORS_PARTNER_TAG",
            ),
            optional_env=(
                "AMAZON_CREATORS_BASE_URL",
                "AMAZON_CREATORS_MARKETPLACE",
            ),
        ),
        ConnectorReadinessSpec(
            connector_id="ebay_browse",
            display_name="eBay Browse API",
            mode_env="EBAY_BROWSE_FIXTURE_MODE",
            default_mode="fixture",
            required_env=(
                "EBAY_BROWSE_CLIENT_ID",
                "EBAY_BROWSE_CLIENT_SECRET",
            ),
            optional_env=("EBAY_BROWSE_MARKETPLACE_ID",),
        ),
        ConnectorReadinessSpec(
            connector_id="idealo_partner",
            display_name="Idealo Partner Feed",
            mode_env="IDEALO_PARTNER_FIXTURE_MODE",
            default_mode="fixture",
            required_env=(
                "IDEALO_PARTNER_ID",
                "IDEALO_PARTNER_API_KEY",
            ),
            optional_env=("IDEALO_MARKETPLACE",),
        ),
        ConnectorReadinessSpec(
            connector_id="affiliate_attribution",
            display_name="Affiliate Attribution",
            mode_env="AFFILIATE_FIXTURE_MODE",
            default_mode="fixture",
            required_env=(
                "AFFILIATE_NETWORK",
                "AFFILIATE_PUBLISHER_ID",
                "AFFILIATE_CAMPAIGN_ID",
            ),
            optional_env=("AFFILIATE_ALLOWED_DOMAINS",),
        ),
    ]

    connectors = []
    for spec in specs:
        mode = _mode(spec, values)
        missing_required = [key for key in spec.required_env if not _present(values, key)]
        production_ready = mode == "production" and not missing_required
        operational_ready = mode in {"mock", "fixture"} or production_ready
        connectors.append(
            {
                "connector_id": spec.connector_id,
                "display_name": spec.display_name,
                "mode": mode,
                "operational_ready": operational_ready,
                "production_ready": production_ready,
                "mock_safe": spec.mock_safe,
                "missing_required_env": missing_required,
                "configured_optional_env": [
                    key for key in spec.optional_env if _present(values, key)
                ],
                "next_action": _next_action(mode, missing_required),
            }
        )

    return {
        "status": "READY" if all(item["operational_ready"] for item in connectors) else "ACTION_REQUIRED",
        "summary": {
            "connector_count": len(connectors),
            "operational_ready_count": sum(1 for item in connectors if item["operational_ready"]),
            "production_ready_count": sum(1 for item in connectors if item["production_ready"]),
            "mock_or_fixture_count": sum(1 for item in connectors if item["mode"] in {"mock", "fixture"}),
            "action_required_count": sum(1 for item in connectors if item["missing_required_env"]),
        },
        "connectors": connectors,
    }


def _next_action(mode: str, missing_required: list[str]) -> str:
    if mode in {"mock", "fixture"}:
        if missing_required:
            return "Mock/fixture calisir; gercek entegrasyon icin eksik env degerlerini tamamla."
        return "Mock/fixture calisir; production moda gecmeden once canli credential dogrula."
    if missing_required:
        return "Production modu secili; eksik env degerlerini tamamla."
    return "Production credential seti tamam; smoke test ile dogrula."
