from app.domains.commerce_ingestion.production_http import (
    ProductionHttpTransport,
)


def test_rc135_transport_has_get_contract():
    transport = ProductionHttpTransport()
    assert callable(transport.get)
