
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class AlertRule:
    user_id:str
    offer_id:str
    rule_type:str
    target_amount:Decimal|None=None
    drop_percent_threshold:Decimal|None=None
    notify_on_back_in_stock:bool=False
    is_active:bool=True
