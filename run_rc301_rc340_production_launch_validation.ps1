$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc301_database_configuration.py `
tests/test_rc302_transaction_boundary.py `
tests/test_rc303_restart_persistence.py `
tests/test_rc304_connection_pool.py `
tests/test_rc305_migration_state.py `
tests/test_rc306_idempotent_write.py `
tests/test_rc307_data_retention.py `
tests/test_rc308_integrity_hash.py `
tests/test_rc309_read_replica.py `
tests/test_rc310_persistence_readiness.py `
tests/test_rc311_connector_smoke.py `
tests/test_rc312_connector_credentials.py `
tests/test_rc313_secret_reference.py `
tests/test_rc314_secret_leak.py `
tests/test_rc315_connector_retry.py `
tests/test_rc316_connector_circuit.py `
tests/test_rc317_connector_rate_limit.py `
tests/test_rc318_connector_readiness.py `
tests/test_rc319_api_rate_limit.py `
tests/test_rc320_authorization.py `
tests/test_rc321_cors.py `
tests/test_rc322_security_headers.py `
tests/test_rc323_password_policy.py `
tests/test_rc324_security_readiness.py `
tests/test_rc325_deployment_register.py `
tests/test_rc326_container_image.py `
tests/test_rc327_tls.py `
tests/test_rc328_health_endpoints.py `
tests/test_rc329_rollback_plan.py `
tests/test_rc330_deployment_readiness.py `
tests/test_rc331_backup_register.py `
tests/test_rc332_backup_verify.py `
tests/test_rc333_restore_drill.py `
tests/test_rc334_disaster_recovery.py `
tests/test_rc335_backup_readiness.py `
tests/test_rc336_production_smoke.py `
tests/test_rc337_load_test.py `
tests/test_rc338_release_check.py `
tests/test_rc339_go_no_go.py `
tests/test_rc340_release_manifest.py `
tests/test_rc301_rc340_production_launch_api.py `
tests/test_rc301_rc340_production_launch_openapi.py `
tests/test_rc301_rc340_production_launch_files.py -q

python -m py_compile app/domains/production_launch/service.py
python -m py_compile app/api/v1/production_launch_router.py
python -m py_compile scripts/production_smoke_test.py
python -m py_compile scripts/check_production_env.py
python -m py_compile scripts/check_release_artifacts.py

python scripts/check_release_artifacts.py
python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
