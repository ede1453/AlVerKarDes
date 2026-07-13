from fastapi import APIRouter

from app.api.v1.ai_decision_pipeline_router import router as ai_decision_pipeline_router
from app.api.v1.ai_explanation_router import router as ai_explanation_router
from app.api.v1.ai_shopping_agent_router import router as ai_shopping_agent_router
from app.api.v1.ai_shopping_assistant_router import router as ai_shopping_assistant_router
from app.api.v1.cache_router import router as cache_router
from app.api.v1.consumer_intelligence_router import router as consumer_intelligence_router
from app.api.v1.crawler_router import router as crawler_router
from app.api.v1.deal_detection_router import router as deal_detection_router
from app.api.v1.decision_context_router import router as decision_context_router
from app.api.v1.decision_memory_router import router as decision_memory_router
from app.api.v1.discount_intelligence_router import router as discount_intelligence_router
from app.api.v1.event_bus_router import router as event_bus_router
from app.api.v1.explanation_router import router as explanation_router
from app.api.v1.feedback_learning_router import router as feedback_learning_router
from app.api.v1.job_queue_router import router as job_queue_router
from app.api.v1.llm_audit_trace_router import router as llm_audit_trace_router
from app.api.v1.llm_explanation_adapter_router import router as llm_explanation_adapter_router
from app.api.v1.llm_orchestration_router import router as llm_orchestration_router
from app.api.v1.llm_provider_gateway_router import router as llm_provider_gateway_router
from app.api.v1.llm_provider_health_router import router as llm_provider_health_router
from app.api.v1.llm_provider_selection_router import router as llm_provider_selection_router
from app.api.v1.llm_streaming_router import router as llm_streaming_router
from app.api.v1.marketplace_aggregation_router import router as marketplace_aggregation_router
from app.api.v1.marketplace_connectors_router import router as marketplace_connectors_router
from app.api.v1.notifications_router import router as notifications_router
from app.api.v1.observability_router import router as observability_router
from app.api.v1.personalization_router import router as personalization_router
from app.api.v1.personalized_intelligence_router import router as personalized_intelligence_router
from app.api.v1.price_history_router import router as price_history_router
from app.api.v1.price_prediction_router import router as price_prediction_router
from app.api.v1.product_canonicalization_router import router as product_canonicalization_router
from app.api.v1.product_matching_router import router as product_matching_router
from app.api.v1.profile_aware_recommendations_router import router as profile_aware_recommendations_router
from app.api.v1.provider_scheduler_router import router as provider_scheduler_router
from app.api.v1.rate_limit_router import router as rate_limit_router
from app.api.v1.recommendation_intelligence_router import router as recommendation_intelligence_router
from app.api.v1.recommendation_router import router as recommendation_router
from app.api.v1.recommendations_router import router as recommendations_router
from app.api.v1.runtime_settings_router import router as runtime_settings_router
from app.api.v1.shopping_pipeline_router import router as shopping_pipeline_router
from app.api.v1.smart_alerts_router import router as smart_alerts_router
from app.api.v1.trust_intelligence_router import router as trust_intelligence_router
from app.api.v1.unified_search_router import router as unified_search_router
from app.api.v1.user_activity_router import router as user_activity_router
from app.api.v1.user_profiles_router import router as user_profiles_router
from app.api.v1.watchlist_router import router as watchlist_router
from app.domains.alerts.router import router as alerts_router
from app.domains.application.grouped_search_recommend_router import router as grouped_search_recommend_router
from app.domains.application.search_recommend_router import router as search_recommend_router
from app.domains.connectors.external_router import router as external_connectors_router
from app.domains.connectors.ingestion_router import router as connector_ingestion_router
from app.domains.connectors.router import router as consumer_connectors_router
from app.domains.deals.router import router as deals_router
from app.domains.identity.router import router as identity_router
from app.domains.integrity.regression_router import router as regression_integrity_router
from app.domains.integrity.router import router as integrity_router
from app.domains.market.connectors.admin_router import router as admin_import_router
from app.domains.market.connectors.router import router as connectors_router
from app.domains.market.router import router as market_router
from app.domains.products.intelligence.merge_candidate_router import router as merge_candidate_router
from app.domains.products.merge_router import router as product_merge_router
from app.domains.products.orphan_cleanup_router import router as orphan_cleanup_router
from app.domains.products.post_merge_router import router as post_merge_router
from app.domains.products.router import router as products_router
from app.domains.system.router import router as system_router
from app.api.v1.notification_outbox_router import router as notification_outbox_router
from app.api.v1.commerce_ingestion_router import router as commerce_ingestion_router
from app.api.v1.commerce_ingestion_execution_router import router as commerce_ingestion_execution_router
from app.api.v1.connector_runtime_router import router as connector_runtime_router
from app.api.v1.connector_operations_router import router as connector_operations_router
from app.api.v1.marketplace_expansion_router import router as marketplace_expansion_router
from app.api.v1.http_connector_router import router as http_connector_router
from app.api.v1.production_http_router import router as production_http_router
from app.api.v1.price_quality_router import router as price_quality_router
from app.api.v1.deal_intelligence_router import router as deal_intelligence_router
from app.api.v1.deal_operations_router import router as deal_operations_router
from app.api.v1.deal_lifecycle_router import router as deal_lifecycle_router
from app.api.v1.deal_persistence_router import router as deal_persistence_router
from app.api.v1.deal_storage_router import router as deal_storage_router
from app.api.v1.deal_storage_sqlalchemy_router import router as deal_storage_sqlalchemy_router
from app.api.v1.deal_storage_resilience_router import router as deal_storage_resilience_router
from app.api.v1.deal_storage_operations_router import router as deal_storage_operations_router
from app.api.v1.storage_reliability_router import router as storage_reliability_router
from app.api.v1.storage_production_readiness_router import router as storage_production_readiness_router
from app.api.v1.commerce_pipeline_router import router as commerce_pipeline_router
from app.api.v1.deal_feed_router import router as deal_feed_router
from app.api.v1.deal_notifications_router import router as deal_notifications_router
from app.api.v1.deal_notification_operations_router import router as deal_notification_operations_router
from app.api.v1.deal_notification_provider_router import router as deal_notification_provider_router
from app.api.v1.consumer_trust_router import router as consumer_trust_router
from app.api.v1.user_value_router import router as user_value_router
from app.api.v1.growth_intelligence_router import router as growth_intelligence_router
from app.api.v1.production_launch_router import router as production_launch_router





api_router = APIRouter()

api_router.include_router(identity_router, prefix="/identity", tags=["identity"])
api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(market_router, prefix="/market", tags=["market"])
api_router.include_router(connectors_router, prefix="/market", tags=["connectors"])
api_router.include_router(admin_import_router, tags=["admin-import"])
api_router.include_router(consumer_connectors_router)
api_router.include_router(connector_ingestion_router)
api_router.include_router(search_recommend_router)
api_router.include_router(grouped_search_recommend_router)
api_router.include_router(product_merge_router)
api_router.include_router(post_merge_router)
api_router.include_router(integrity_router)
api_router.include_router(system_router)
api_router.include_router(regression_integrity_router)
api_router.include_router(orphan_cleanup_router)
api_router.include_router(external_connectors_router)
api_router.include_router(alerts_router)
api_router.include_router(merge_candidate_router)
api_router.include_router(deals_router)
api_router.include_router(recommendation_router)
api_router.include_router(recommendation_intelligence_router)
api_router.include_router(consumer_intelligence_router)
api_router.include_router(ai_decision_pipeline_router)
api_router.include_router(decision_context_router)
api_router.include_router(explanation_router)
api_router.include_router(decision_memory_router)
api_router.include_router(personalized_intelligence_router)
api_router.include_router(feedback_learning_router)
api_router.include_router(trust_intelligence_router)
api_router.include_router(ai_shopping_assistant_router)
api_router.include_router(llm_explanation_adapter_router)
api_router.include_router(llm_provider_gateway_router)
api_router.include_router(llm_audit_trace_router)
api_router.include_router(llm_orchestration_router)
api_router.include_router(llm_provider_health_router)
api_router.include_router(llm_provider_selection_router)
api_router.include_router(llm_streaming_router)
api_router.include_router(observability_router)
api_router.include_router(rate_limit_router)
api_router.include_router(cache_router)
api_router.include_router(job_queue_router)
api_router.include_router(event_bus_router)
api_router.include_router(provider_scheduler_router)
api_router.include_router(marketplace_aggregation_router)
api_router.include_router(unified_search_router)
api_router.include_router(product_matching_router)
api_router.include_router(price_history_router)
api_router.include_router(personalization_router)
api_router.include_router(ai_shopping_agent_router)
api_router.include_router(deal_detection_router)
api_router.include_router(price_prediction_router)
api_router.include_router(smart_alerts_router)
api_router.include_router(watchlist_router)
api_router.include_router(discount_intelligence_router)
api_router.include_router(ai_explanation_router)
api_router.include_router(marketplace_connectors_router)
api_router.include_router(crawler_router)
api_router.include_router(product_canonicalization_router)
api_router.include_router(recommendations_router)
api_router.include_router(notifications_router)
api_router.include_router(user_activity_router)
api_router.include_router(user_profiles_router)
api_router.include_router(profile_aware_recommendations_router)
api_router.include_router(shopping_pipeline_router)
api_router.include_router(runtime_settings_router)
api_router.include_router(notification_outbox_router)
api_router.include_router(commerce_ingestion_router)
api_router.include_router(commerce_ingestion_execution_router)
api_router.include_router(connector_runtime_router)
api_router.include_router(connector_operations_router)
api_router.include_router(marketplace_expansion_router)
api_router.include_router(http_connector_router)
api_router.include_router(production_http_router)
api_router.include_router(price_quality_router)
api_router.include_router(deal_intelligence_router)
api_router.include_router(deal_operations_router)
api_router.include_router(deal_lifecycle_router)
api_router.include_router(deal_persistence_router)
api_router.include_router(deal_storage_router)
api_router.include_router(deal_storage_sqlalchemy_router)
api_router.include_router(deal_storage_resilience_router)
api_router.include_router(deal_storage_operations_router)
api_router.include_router(storage_reliability_router)
api_router.include_router(storage_production_readiness_router)
api_router.include_router(commerce_pipeline_router)
api_router.include_router(deal_feed_router)
api_router.include_router(deal_notifications_router)
api_router.include_router(deal_notification_operations_router)
api_router.include_router(deal_notification_provider_router)
api_router.include_router(consumer_trust_router)
api_router.include_router(user_value_router)
api_router.include_router(growth_intelligence_router)
api_router.include_router(production_launch_router)

