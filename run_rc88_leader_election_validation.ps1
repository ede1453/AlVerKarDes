$ErrorActionPreference = "Stop"

python -m pytest tests/test_rc88_leader_election_service.py tests/test_rc88_leader_election_api.py tests/test_rc88_leader_election_openapi.py tests/test_rc88_leader_election_vertical_slice.py -q
python -m py_compile app/domains/notifications/outbox/outbox_service.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
