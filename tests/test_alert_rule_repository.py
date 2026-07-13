
from app.domains.alerts.models import AlertRule
from app.domains.alerts.repository import AlertRuleRepository


def test_active_rules():
    repo=AlertRuleRepository()
    repo.add(AlertRule(user_id="u1",offer_id="o1",rule_type="TARGET_PRICE"))
    repo.add(AlertRule(user_id="u2",offer_id="o2",rule_type="TARGET_PRICE",is_active=False))
    assert len(repo.list_active())==1
