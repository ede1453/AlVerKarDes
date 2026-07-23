from app.domains.price_history.price_history_models import PricePoint


class InMemoryPriceHistoryRepository:
    def __init__(self):
        self._points: list[PricePoint] = []

    def add(self, point: PricePoint) -> PricePoint:
        self._points.append(point)
        return point

    def list_for_product(self, product_key: str):
        return sorted(
            [point for point in self._points if point.product_key == product_key],
            key=lambda point: point.observed_at,
        )

    def clear(self):
        self._points.clear()

    def count(self):
        return len(self._points)
