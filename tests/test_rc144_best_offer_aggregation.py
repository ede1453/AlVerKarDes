from app.domains.commerce_ingestion.price_quality import BestOfferAggregator


def test_rc144_best_offer_selection():
    result = BestOfferAggregator().select(
        offers=[
            {
                "source_id":"a",
                "price":900,
                "normalized_price":900,
                "shipping_cost":20,
                "source_confidence":80,
                "usable":True,
                "anomalous":False,
            },
            {
                "source_id":"b",
                "price":910,
                "normalized_price":910,
                "shipping_cost":0,
                "source_confidence":90,
                "usable":True,
                "anomalous":False,
            },
        ]
    )
    assert result["selected"] is True
    assert result["best_offer"]["source_id"] == "b"
    assert result["best_offer"]["effective_price"] == 910.0
