from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass
class PricePoint:
    amount: float
    currency: str = "EUR"
    observed_at: str | None = None


@dataclass
class PriceIntelligenceResult:
    current_price: float
    currency: str
    historical_lowest: float
    historical_highest: float
    historical_average: float
    history_points: int
    discount_from_average_pct: float
    position_score: float
    volatility_score: float
    fake_discount_risk: str
    signal: str
    confidence: float
    explanation: str


class PriceHistoryAnalyzer:
    def analyze(self, points: list[PricePoint]) -> PriceIntelligenceResult:
        if not points:
            raise ValueError("Price history is empty.")

        amounts = [float(point.amount) for point in points]
        current = amounts[-1]
        lowest = min(amounts)
        highest = max(amounts)
        avg = mean(amounts)
        currency = points[-1].currency or "EUR"

        discount_from_average_pct = self._pct((avg - current), avg)
        position_score = self._position_score(current=current, lowest=lowest, highest=highest)
        volatility_score = self._volatility_score(amounts)
        fake_discount_risk = self._fake_discount_risk(
            amounts=amounts,
            current=current,
            avg=avg,
            highest=highest,
        )
        signal, explanation = self._signal(
            current=current,
            lowest=lowest,
            avg=avg,
            position_score=position_score,
            fake_discount_risk=fake_discount_risk,
            history_points=len(amounts),
        )
        confidence = self._confidence(
            history_points=len(amounts),
            position_score=position_score,
            volatility_score=volatility_score,
            fake_discount_risk=fake_discount_risk,
        )

        return PriceIntelligenceResult(
            current_price=round(current, 2),
            currency=currency,
            historical_lowest=round(lowest, 2),
            historical_highest=round(highest, 2),
            historical_average=round(avg, 2),
            history_points=len(amounts),
            discount_from_average_pct=round(discount_from_average_pct, 2),
            position_score=round(position_score, 2),
            volatility_score=round(volatility_score, 2),
            fake_discount_risk=fake_discount_risk,
            signal=signal,
            confidence=round(confidence, 2),
            explanation=explanation,
        )

    def _pct(self, value: float, denominator: float) -> float:
        if denominator == 0:
            return 0.0
        return (value / denominator) * 100

    def _position_score(self, *, current: float, lowest: float, highest: float) -> float:
        if highest == lowest:
            return 50.0

        # 100 means current is at historical low. 0 means current is at historical high.
        return max(0.0, min(100.0, ((highest - current) / (highest - lowest)) * 100))

    def _volatility_score(self, amounts: list[float]) -> float:
        if len(amounts) < 2:
            return 0.0

        avg = mean(amounts)
        if avg == 0:
            return 0.0

        coefficient = pstdev(amounts) / avg
        return max(0.0, min(100.0, coefficient * 100))

    def _fake_discount_risk(self, *, amounts: list[float], current: float, avg: float, highest: float) -> str:
        if len(amounts) < 5:
            return "UNKNOWN"

        baseline = min(amounts[0], amounts[1])
        peak = max(amounts)
        peak_index = amounts.index(peak)

        # Pattern: normal price -> artificial spike -> back near normal.
        if (
            peak_index >= 2
            and peak >= baseline * 1.25
            and current <= baseline * 1.05
        ):
            return "HIGH"

        previous = amounts[:-3] or amounts
        previous_avg = mean(previous)

        if current >= previous_avg * 0.97:
            return "MEDIUM"

        return "LOW"

    def _signal(
        self,
        *,
        current: float,
        lowest: float,
        avg: float,
        position_score: float,
        fake_discount_risk: str,
        history_points: int,
    ) -> tuple[str, str]:
        if history_points < 3:
            return "INSUFFICIENT_HISTORY", "Not enough price history."

        if fake_discount_risk == "HIGH":
            return "WAIT", "Price pattern suggests possible fake discount."

        if current <= lowest * 1.03 and position_score >= 85:
            return "BUY", "Current price is near historical low."

        if current < avg * 0.90 and position_score >= 70:
            return "BUY", "Current price is meaningfully below historical average."

        if current > avg * 1.05:
            return "WAIT", "Current price is above historical average."

        return "NEUTRAL", "Current price is not clearly good or bad."

    def _confidence(
        self,
        *,
        history_points: int,
        position_score: float,
        volatility_score: float,
        fake_discount_risk: str,
    ) -> float:
        base = min(80.0, 20.0 + history_points * 7.5)

        if position_score >= 85:
            base += 10

        if volatility_score > 20:
            base -= 10

        if fake_discount_risk == "HIGH":
            base -= 20
        elif fake_discount_risk == "UNKNOWN":
            base -= 10

        return max(0.0, min(100.0, base))
