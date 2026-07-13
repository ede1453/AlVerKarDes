import json
import re
from decimal import Decimal

from app.domains.connectors.external_contract import ExternalConnectorOffer


class AmazonProductParser:
    source = "amazon-de"

    def parse_json_items(self, raw_json: str) -> list[ExternalConnectorOffer]:
        payload = json.loads(raw_json)

        items = payload.get("items") or payload.get("products") or payload.get("search_results") or []
        results: list[ExternalConnectorOffer] = []

        for item in items:
            offer = self._parse_item(item)
            if offer:
                results.append(offer)

        return results

    def _parse_item(self, item: dict) -> ExternalConnectorOffer | None:
        title = item.get("title") or item.get("name")
        url = item.get("url") or item.get("product_url")
        price = item.get("price") or item.get("amount")
        currency = item.get("currency") or "EUR"

        if not title or not url or price is None:
            return None

        return ExternalConnectorOffer(
            source=self.source,
            title=str(title).strip(),
            url=str(url).strip(),
            price=self._decimal(price),
            currency=str(currency),
            availability=item.get("availability") or item.get("stock_status") or "unknown",
            brand=item.get("brand"),
            gtin=item.get("gtin"),
            sku=item.get("asin") or item.get("sku"),
            confidence=float(item.get("confidence") or 80),
        )

    def _decimal(self, value) -> Decimal:
        if isinstance(value, Decimal):
            return value

        text = str(value).strip()
        text = text.replace("€", "").replace("EUR", "").strip()
        text = re.sub(r"[^0-9,.]", "", text)

        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")

        return Decimal(text)
