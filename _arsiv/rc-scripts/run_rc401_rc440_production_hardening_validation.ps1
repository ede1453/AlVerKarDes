$ErrorActionPreference = "Stop"

python -m py_compile app/core/production_hardening.py
python -m py_compile app/core/security_middleware.py
python -m py_compile app/core/config.py
python -m py_compile app/main.py
python -m py_compile scripts/audit_platform_readiness.py
python -m py_compile scripts/build_sanitized_release.py
python -m py_compile scripts/check_production_hardening.py

python -m pytest `
  tests/test_rc401_secret_file_guard.py `
  tests/test_rc402_example_env_allowed.py `
  tests/test_rc403_git_excluded.py `
  tests/test_rc404_venv_excluded.py `
  tests/test_rc405_cache_excluded.py `
  tests/test_rc406_nested_zip_excluded.py `
  tests/test_rc407_log_excluded.py `
  tests/test_rc408_placeholder_detection.py `
  tests/test_rc409_real_value_not_placeholder.py `
  tests/test_rc410_jwt_strength.py `
  tests/test_rc411_weak_jwt.py `
  tests/test_rc412_cors_parse.py `
  tests/test_rc413_cors_wildcard.py `
  tests/test_rc414_cors_https.py `
  tests/test_rc415_trusted_hosts.py `
  tests/test_rc416_trusted_wildcard.py `
  tests/test_rc417_database_url.py `
  tests/test_rc418_database_localhost.py `
  tests/test_rc419_redis_url.py `
  tests/test_rc420_redis_localhost.py `
  tests/test_rc421_fixture_guard.py `
  tests/test_rc422_fixture_local_allowed.py `
  tests/test_rc423_amazon_credentials.py `
  tests/test_rc424_ebay_credentials.py `
  tests/test_rc425_idealo_credentials.py `
  tests/test_rc426_affiliate_credentials.py `
  tests/test_rc427_redaction.py `
  tests/test_rc428_non_secret_visible.py `
  tests/test_rc429_security_headers.py `
  tests/test_rc430_hsts_production.py `
  tests/test_rc431_public_routes.py `
  tests/test_rc432_unprotected_write.py `
  tests/test_rc433_protected_write.py `
  tests/test_rc434_environment_ready.py `
  tests/test_rc435_debug_blocked.py `
  tests/test_rc436_request_size_setting.py `
  tests/test_rc437_version_contract.py `
  tests/test_rc438_main_cors_contract.py `
  tests/test_rc439_main_trusted_host_contract.py `
  tests/test_rc440_sanitized_builder_contract.py -q

python scripts/check_openapi_uniqueness.py
python scripts/api_contract_schema_guard.py
python scripts/audit_platform_readiness.py
python -m pytest -q
