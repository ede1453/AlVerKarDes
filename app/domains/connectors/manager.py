import asyncio
from dataclasses import dataclass, field

from app.domains.connectors.sdk import ConnectorProductResult, StoreConnector
from app.domains.products.canonical_service import CanonicalProductService
from app.domains.products.matching_engine import ProductMatchEngine


@dataclass
class UnifiedOffer:
    source: str
    title: str
    canonical_key: str
    url: str | None = None
    price: float | None = None
    currency: str = "EUR"
    availability: str | None = None
    brand: str | None = None
    gtin: str | None = None
    sku: str | None = None
    connector_confidence: float = 0.0
    canonical_confidence: float = 0.0
    overall_confidence: float = 0.0
    raw: dict | None = None
    match_basis: list[str] = field(default_factory=list)
    match_group_id: str | None = None
    match_group_score: float | None = None
    is_real_data: bool = True


@dataclass
class ConnectorSearchResult:
    query: str
    country: str
    offers: list[UnifiedOffer]
    errors: list[dict] = field(default_factory=list)


class ConnectorManager:
    def __init__(self, connectors: list[StoreConnector]):
        self.connectors = connectors
        self.canonical_service = CanonicalProductService()
        self.match_engine = ProductMatchEngine()

    async def search_all(self, query: str, country: str = "DE") -> ConnectorSearchResult:
        tasks = [self._safe_search(connector, query, country) for connector in self.connectors]
        results = await asyncio.gather(*tasks)

        raw_items: list[ConnectorProductResult] = []
        errors: list[dict] = []

        for connector_items, connector_errors in results:
            raw_items.extend(connector_items)
            errors.extend(connector_errors)

        unified = [self._to_unified_offer(item, country) for item in raw_items]
        grouped = self._assign_match_groups(unified, country=country)
        deduped = self._dedupe(grouped)

        deduped.sort(
            key=lambda item: (
                item.price is None,
                item.price if item.price is not None else 10**12,
                -item.overall_confidence,
            )
        )

        return ConnectorSearchResult(query=query, country=country, offers=deduped, errors=errors)

    async def _safe_search(self, connector: StoreConnector, query: str, country: str) -> tuple[list[ConnectorProductResult], list[dict]]:
        try:
            items = await connector.search(query=query, country=country)
            return items, []
        except Exception as exc:
            return [], [{
                "connector": getattr(connector, "source_name", connector.__class__.__name__),
                "error": str(exc),
            }]

    def _to_unified_offer(self, item: ConnectorProductResult, country: str) -> UnifiedOffer:
        canonical = self.canonical_service.build_match(item.title, country=country)

        overall = self._score_offer(
            connector_confidence=item.confidence,
            canonical_confidence=canonical.confidence,
            has_price=item.price is not None,
            has_url=item.url is not None,
            has_gtin=item.gtin is not None,
        )

        return UnifiedOffer(
            source=item.source,
            title=item.title,
            canonical_key=canonical.canonical_key,
            url=item.url,
            price=item.price,
            currency=item.currency,
            availability=item.availability,
            brand=item.brand or canonical.identity.brand,
            gtin=item.gtin,
            sku=item.sku,
            connector_confidence=item.confidence,
            canonical_confidence=canonical.confidence,
            overall_confidence=overall,
            raw=item.raw,
            match_basis=canonical.match_basis,
            is_real_data=item.is_real_data,
        )

    def _assign_match_groups(self, offers: list[UnifiedOffer], country: str = "DE") -> list[UnifiedOffer]:
        groups: list[list[UnifiedOffer]] = []

        for offer in offers:
            placed = False

            for group in groups:
                representative = group[0]
                match = self.match_engine.compare(representative.title, offer.title, country=country)

                if match.same_product:
                    offer.match_group_id = representative.match_group_id
                    offer.match_group_score = match.final_score
                    group.append(offer)
                    placed = True
                    break

            if not placed:
                offer.match_group_id = self._new_group_id(offer, len(groups) + 1)
                offer.match_group_score = 100.0
                groups.append([offer])

        return offers

    def _new_group_id(self, offer: UnifiedOffer, index: int) -> str:
        if offer.gtin:
            return f"gtin::{offer.gtin}"
        if offer.canonical_key:
            return f"group::{offer.canonical_key}"
        return f"group::{index}"

    def _score_offer(self, *, connector_confidence: float, canonical_confidence: float, has_price: bool, has_url: bool, has_gtin: bool) -> float:
        score = 0.0
        score += min(connector_confidence, 100) * 0.35
        score += min(canonical_confidence, 100) * 0.45
        score += 10 if has_price else 0
        score += 5 if has_url else 0
        score += 5 if has_gtin else 0
        return min(round(score, 2), 100.0)

    def _dedupe(self, offers: list[UnifiedOffer]) -> list[UnifiedOffer]:
        best_by_key: dict[str, UnifiedOffer] = {}

        for offer in offers:
            key = self._dedupe_key(offer)

            if key not in best_by_key:
                best_by_key[key] = offer
                continue

            current = best_by_key[key]
            if self._is_better_offer(offer, current):
                best_by_key[key] = offer

        return list(best_by_key.values())

    def _dedupe_key(self, offer: UnifiedOffer) -> str:
        if offer.gtin:
            return f"gtin::{offer.gtin}"
        if offer.url:
            return f"url::{offer.url}"
        if offer.source and offer.sku:
            return f"sku::{offer.source}::{offer.sku}"
        return f"fallback::{offer.source}::{offer.title}::{offer.price}"

    def _is_better_offer(self, candidate: UnifiedOffer, current: UnifiedOffer) -> bool:
        if candidate.overall_confidence > current.overall_confidence:
            return True

        if candidate.overall_confidence == current.overall_confidence:
            if candidate.price is not None and current.price is None:
                return True
            if candidate.price is not None and current.price is not None:
                return candidate.price < current.price

        return False
