$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

python .\scripts\integrate_authentication_core.py

python -m py_compile `
  app/domains/auth_core/types.py
python -m py_compile `
  app/domains/auth_core/models.py
python -m py_compile `
  app/domains/auth_core/schemas.py
python -m py_compile `
  app/domains/auth_core/password_policy.py
python -m py_compile `
  app/domains/auth_core/tokens.py
python -m py_compile `
  app/domains/auth_core/repository.py
python -m py_compile `
  app/domains/auth_core/service.py
python -m py_compile `
  app/domains/auth_core/dependencies.py
python -m py_compile `
  app/api/v1/auth_core_router.py
python -m py_compile `
  alembic/versions/0015_authentication_core.py

python -m pytest `
  tests/test_rc441_password_policy.py `
  tests/test_rc442_access_token_claims.py `
  tests/test_rc443_refresh_token_storage.py `
  tests/test_rc444_refresh_rotation_contract.py `
  tests/test_rc445_session_management_contract.py `
  tests/test_rc446_login_lockout_contract.py `
  tests/test_rc447_email_verification_contract.py `
  tests/test_rc448_password_reset_contract.py `
  tests/test_rc449_auth_audit_contract.py `
  tests/test_rc450_authentication_core_openapi.py `
  tests/test_rc441_rc450_migration_contract.py `
  tests/test_rc441_rc450_models_contract.py -q

python .\scripts\check_authentication_core_integration.py
python .\scripts\check_openapi_uniqueness.py
python .\scripts\api_contract_snapshot.py
python .\scripts\api_contract_schema_guard.py
python -m pytest -q
