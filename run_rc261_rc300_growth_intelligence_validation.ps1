$ErrorActionPreference = "Stop"

python -m pytest `
tests/test_rc261_cac.py `
tests/test_rc262_ltv.py `
tests/test_rc263_ltv_cac.py `
tests/test_rc264_mau.py `
tests/test_rc265_dau.py `
tests/test_rc266_stickiness.py `
tests/test_rc267_activation.py `
tests/test_rc268_retention.py `
tests/test_rc269_churn.py `
tests/test_rc270_growth_funnel.py `
tests/test_rc271_affiliate_click.py `
tests/test_rc272_affiliate_conversion.py `
tests/test_rc273_affiliate_conversion_rate.py `
tests/test_rc274_revenue_per_click.py `
tests/test_rc275_revenue_per_user.py `
tests/test_rc276_revenue_independence.py `
tests/test_rc277_campaign_create.py `
tests/test_rc278_campaign_spend.py `
tests/test_rc279_campaign_roi.py `
tests/test_rc280_campaign_budget.py `
tests/test_rc281_segment_create.py `
tests/test_rc282_segment_membership.py `
tests/test_rc283_behavioral_segment.py `
tests/test_rc284_cohort_create.py `
tests/test_rc285_cohort_retention.py `
tests/test_rc286_reactivation.py `
tests/test_rc287_retailer_snapshot.py `
tests/test_rc288_retailer_quality.py `
tests/test_rc289_retailer_conversion.py `
tests/test_rc290_retailer_scorecard.py `
tests/test_rc291_experiment_create.py `
tests/test_rc292_experiment_result.py `
tests/test_rc293_experiment_evaluate.py `
tests/test_rc294_growth_event.py `
tests/test_rc295_north_star.py `
tests/test_rc296_gmv.py `
tests/test_rc297_take_rate.py `
tests/test_rc298_revenue_quality.py `
tests/test_rc299_growth_health.py `
tests/test_rc300_executive_dashboard.py `
tests/test_rc261_rc300_growth_intelligence_api.py `
tests/test_rc261_rc300_growth_intelligence_openapi.py -q

python -m py_compile app/domains/growth_intelligence/service.py
python -m py_compile app/api/v1/growth_intelligence_router.py

python scripts/check_docker_db_env_consistency.py
python scripts/check_openapi_uniqueness.py
python scripts/api_contract_snapshot.py
python scripts/api_contract_schema_guard.py
python -m pytest -q
