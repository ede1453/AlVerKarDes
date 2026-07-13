from app.domains.connectors.external_contract import ExternalConnectorOffer
from app.domains.connectors.manager import ConnectorProductResult


class ExternalOfferMapper:
    def to_connector_product_result(self, offer: ExternalConnectorOffer) -> ConnectorProductResult:
        return ConnectorProductResult(
            source=offer.source,
            title=offer.title,
            url=offer.url,
            price=float(offer.price),
            currency=offer.currency,
            availability=offer.availability,
            brand=offer.brand,
            gtin=offer.gtin,
            sku=offer.sku,
            confidence=offer.confidence,
        )

    def many_to_connector_product_results(self, offers: list[ExternalConnectorOffer]) -> list[ConnectorProductResult]:
        return [self.to_connector_product_result(offer) for offer in offers]
