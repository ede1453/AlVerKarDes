from app.domains.shopping_pipeline.pipeline_service import ShoppingPipelineService


class DummyMarketplaceService:
    def aggregate(self, payload):
        return {
            "query": payload["query"],
            "normalized_query": payload["query"].lower(),
            "offer_count": len(payload["offers"]),
            "marketplaces": [offer.get("marketplace") for offer in payload["offers"]],
            "min_price": "949.00",
            "max_price": "999.00",
            "currency": "EUR",
            "offers": payload["offers"],
        }


def test_rc571_pipeline_accepts_injected_marketplace_service():
    service = ShoppingPipelineService(marketplace_service=DummyMarketplaceService())

    result = service.run(
        {
            "user_id": "user-1",
            "query": "MacBook Air M3 13 inch 512GB",
            "profile_context": {
                "user_id": "user-1",
                "preferred_marketplaces": ["saturn"],
                "preferred_brands": ["Apple"],
                "preferred_product_keys": [],
                "avoided_product_keys": [],
                "blocked_marketplaces": [],
                "risk_tolerance": "LOW",
                "profile_score": 60,
                "metadata": {"context_version": "user_profile_context_v1"},
            },
            "offers": [
                {
                    "marketplace": "saturn",
                    "seller": "Saturn",
                    "product_name": "Apple MacBook Air M3 13 inch 512GB",
                    "price": "949.00",
                    "currency": "EUR",
                }
            ],
            "claimed_original_price": "1099.00",
        }
    )

    assert result["status"] == "COMPLETED"
    assert result["search"]["offer_count"] == 1
