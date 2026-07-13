from app.domains.connectors.external_offer_mapper import ExternalOfferMapper


class ExternalConnectorBridge:
    def __init__(self, external_connectors, mapper: ExternalOfferMapper | None = None):
        self.external_connectors = external_connectors
        self.mapper = mapper or ExternalOfferMapper()

    async def search_all(self, query: str, country: str = "DE"):
        results = []
        errors = []

        for connector in self.external_connectors:
            try:
                external_offers = await connector.search(query=query, country=country)
                results.extend(
                    self.mapper.many_to_connector_product_results(external_offers)
                )
            except Exception as exc:
                errors.append(
                    {
                        "source": getattr(connector, "source", "unknown"),
                        "error": str(exc),
                    }
                )

        return {
            "query": query,
            "country": country,
            "results": results,
            "errors": errors,
        }
