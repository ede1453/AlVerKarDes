from app.domains.alerts.db_models import AlertRuleModel
from app.domains.alerts.schemas import AlertRuleCreate, AlertRuleRead


def test_alert_rule_model_table_name():
    assert AlertRuleModel.__tablename__ == "alert_rules"


def test_alert_rule_create_schema_fields():
    fields = AlertRuleCreate.model_fields

    assert "user_id" in fields
    assert "offer_id" in fields
    assert "rule_type" in fields
    assert "target_amount" in fields
    assert "drop_percent_threshold" in fields
    assert "notify_on_back_in_stock" in fields


def test_alert_rule_read_from_attributes_enabled():
    assert AlertRuleRead.model_config["from_attributes"] is True
