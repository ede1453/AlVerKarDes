
class AlertRuleRepository:
    def __init__(self):
        self._items=[]

    def add(self, rule):
        self._items.append(rule)
        return rule

    def list_active(self):
        return [r for r in self._items if r.is_active]
