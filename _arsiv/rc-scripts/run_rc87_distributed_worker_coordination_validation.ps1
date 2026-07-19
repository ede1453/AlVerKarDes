$ErrorActionPreference = "Stop"

python -m pytest tests/test_rc87_distributed_worker_coordination_service.py tests/test_rc87_distributed_worker_coordination_api.py tests/test_rc87_distributed_worker_coordination_openapi.py tests/test_rc87_distributed_worker_coordination_vertical_slice.py -q
python -m py_compile app/domains/notifications/outbox/outbox_service.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
