$ErrorActionPreference = "Stop"

python -m py_compile .\app\api\v1\marketplace_connectors_router.py
python -m py_compile .\scripts\verify_connector_source_parity.py

python -m pytest `
  tests/test_rc49_marketplace_connector_api_contract.py `
  tests/test_rc49_marketplace_connector_openapi.py `
  tests/test_rc49_marketplace_connector_vertical_slice.py `
  tests/test_connector_hotfix_v11_rc49_contract.py `
  tests/test_connector_hotfix_v11_vertical_slice.py `
  tests/test_connector_hotfix_router_registration.py `
  tests/test_connector_hotfix_amazon_fixture_isolation.py `
  tests/test_rc361_rc400_marketplace_connectors_api.py `
  tests/test_rc361_rc400_marketplace_connectors_openapi.py -q

python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
