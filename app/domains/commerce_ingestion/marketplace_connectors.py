from typing import Any


class MarketplaceConnectorError(RuntimeError):
    pass

class AmazonConnector:
    marketplace = "amazon"
    def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "marketplace": self.marketplace,
            "external_offer_id": str(item.get("asin") or item.get("id") or ""),
            "product_title": item.get("title") or "",
            "product_url": item.get("detail_page_url") or item.get("url") or "",
            "price": item.get("price"),
            "currency": item.get("currency", "EUR"),
            "availability": item.get("availability", "unknown"),
            "seller_name": item.get("merchant_name"),
            "canonical_product_key": item.get("canonical_product_key"),
            "observed_at": item.get("observed_at"),
            "raw_payload": item,
        }

class EbayConnector:
    marketplace = "ebay"
    def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        price = item.get("price")
        currency = item.get("currency", "EUR")
        if isinstance(price, dict):
            currency = price.get("currency", currency)
            price = price.get("value")
        seller = item.get("seller")
        return {
            "marketplace": self.marketplace,
            "external_offer_id": str(item.get("itemId") or item.get("id") or ""),
            "product_title": item.get("title") or "",
            "product_url": item.get("itemWebUrl") or item.get("url") or "",
            "price": price,
            "currency": currency,
            "availability": item.get("availabilityStatus", "unknown"),
            "seller_name": seller.get("username") if isinstance(seller, dict) else None,
            "canonical_product_key": item.get("canonical_product_key"),
            "observed_at": item.get("observed_at"),
            "raw_payload": item,
        }

class IdealoConnector:
    marketplace = "idealo"
    def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "marketplace": self.marketplace,
            "external_offer_id": str(item.get("offerId") or item.get("id") or ""),
            "product_title": item.get("productName") or item.get("title") or "",
            "product_url": item.get("offerUrl") or item.get("url") or "",
            "price": item.get("totalPrice", item.get("price")),
            "currency": item.get("currency", "EUR"),
            "availability": item.get("deliveryStatus", "unknown"),
            "seller_name": item.get("shopName"),
            "canonical_product_key": item.get("canonical_product_key"),
            "observed_at": item.get("observed_at"),
            "raw_payload": item,
        }

class AffiliateNetworkConnector:
    marketplace = "affiliate"
    def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "marketplace": item.get("network") or self.marketplace,
            "external_offer_id": str(item.get("offer_id") or item.get("id") or ""),
            "product_title": item.get("product_name") or item.get("title") or "",
            "product_url": item.get("tracking_url") or item.get("url") or "",
            "price": item.get("sale_price", item.get("price")),
            "currency": item.get("currency", "EUR"),
            "availability": item.get("availability", "unknown"),
            "seller_name": item.get("advertiser_name"),
            "canonical_product_key": item.get("canonical_product_key"),
            "observed_at": item.get("observed_at"),
            "raw_payload": item,
        }

class MarketplaceConnectorFactory:
    MAP = {
        "amazon": AmazonConnector,
        "ebay": EbayConnector,
        "idealo": IdealoConnector,
        "affiliate": AffiliateNetworkConnector,
    }

    @classmethod
    def create(cls, marketplace: str):
        connector = cls.MAP.get(marketplace.lower())
        if connector is None:
            raise MarketplaceConnectorError("UNSUPPORTED_MARKETPLACE")
        return connector()

class MarketplaceScoreEngine:
    def calculate(
        self,
        current_price: float,
        historical_average_price: float | None,
        store_trust_score: int,
        availability: str,
        shipping_cost: float = 0.0,
        review_score: float | None = None,
    ) -> dict[str, Any]:
        if current_price <= 0:
            return {"score": 0, "grade": "REJECT", "reasons": ["INVALID_CURRENT_PRICE"]}

        effective_price = float(current_price) + max(float(shipping_cost), 0.0)
        score = 0.0
        reasons = []

        if historical_average_price and historical_average_price > 0:
            ratio = max(0.0, (historical_average_price - effective_price) / historical_average_price)
            score += min(50.0, ratio * 100)
            reasons.append(f"PRICE_ADVANTAGE_{round(ratio * 100, 2)}")
        else:
            reasons.append("NO_HISTORICAL_AVERAGE")

        trust = min(max(store_trust_score, 0), 100)
        score += trust * 0.3
        reasons.append(f"STORE_TRUST_{trust}")

        if availability.lower() in {"in_stock", "available", "ships_immediately"}:
            score += 10
            reasons.append("AVAILABLE_NOW")

        if review_score is not None:
            bounded = min(max(float(review_score), 0.0), 5.0)
            score += bounded * 2
            reasons.append(f"REVIEW_SCORE_{bounded}")

        final = round(min(score, 100.0), 2)
        grade = "EXCELLENT" if final >= 80 else "GOOD" if final >= 65 else "FAIR" if final >= 50 else "WEAK"
        return {
            "score": final,
            "grade": grade,
            "effective_price": effective_price,
            "reasons": reasons,
            "metadata": {"score_version": "marketplace_score_v1"},
        }
