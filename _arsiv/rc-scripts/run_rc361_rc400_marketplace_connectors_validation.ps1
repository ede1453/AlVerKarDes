$ErrorActionPreference="Stop"
python -m pytest `
tests/test_rc361_ebay_configuration.py `
tests/test_rc362_ebay_basic_auth.py `
tests/test_rc363_ebay_token.py `
tests/test_rc364_ebay_headers.py `
tests/test_rc365_ebay_search_params.py `
tests/test_rc366_ebay_normalize_item.py `
tests/test_rc367_ebay_normalize_search.py `
tests/test_rc368_ebay_error_mapping.py `
tests/test_rc369_ebay_retry_delay.py `
tests/test_rc370_ebay_execute.py `
tests/test_rc371_ebay_search.py `
tests/test_rc372_ebay_get_item.py `
tests/test_rc373_ebay_snapshots.py `
tests/test_rc374_ebay_affiliate_url.py `
tests/test_rc375_ebay_dedup.py `
tests/test_rc376_ebay_ingestion.py `
tests/test_rc377_ebay_metrics.py `
tests/test_rc378_ebay_health.py `
tests/test_rc379_ebay_collection.py `
tests/test_rc380_ebay_readiness.py `
tests/test_rc381_idealo_configuration.py `
tests/test_rc382_idealo_csv.py `
tests/test_rc383_idealo_json.py `
tests/test_rc384_idealo_normalize.py `
tests/test_rc385_idealo_validate.py `
tests/test_rc386_idealo_feed_normalize.py `
tests/test_rc387_idealo_dedup.py `
tests/test_rc388_idealo_snapshots.py `
tests/test_rc389_idealo_collection.py `
tests/test_rc390_idealo_health.py `
tests/test_rc391_affiliate_configuration.py `
tests/test_rc392_affiliate_tracking_url.py `
tests/test_rc393_affiliate_click.py `
tests/test_rc394_affiliate_conversion.py `
tests/test_rc395_affiliate_duplicate.py `
tests/test_rc396_affiliate_conversion_rate.py `
tests/test_rc397_affiliate_revenue.py `
tests/test_rc398_affiliate_disclosure.py `
tests/test_rc399_affiliate_audit.py `
tests/test_rc400_affiliate_readiness.py `
tests/test_rc361_rc400_marketplace_connectors_api.py `
tests/test_rc361_rc400_marketplace_connectors_openapi.py -q
python -m py_compile app/domains/marketplace_connectors/service.py
python -m py_compile app/api/v1/marketplace_connectors_router.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
