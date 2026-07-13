from enum import StrEnum


class RecommendationDecision(StrEnum):
    BUY = "BUY"
    WAIT = "WAIT"
    CONSIDER_ALTERNATIVE = "CONSIDER_ALTERNATIVE"
    DO_NOT_BUY = "DO_NOT_BUY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
