from app.domains.commerce_ingestion.price_quality import SourceTrustReconciler


def test_rc143_source_trust_reconciliation():
    result = SourceTrustReconciler().reconcile(
        offers=[
            {
                "source_id":"a",
                "price":900,
                "source_trust_score":70,
                "verified_source":False,
                "anomalous":False,
            },
            {
                "source_id":"b",
                "price":950,
                "source_trust_score":80,
                "verified_source":True,
                "anomalous":False,
            },
        ]
    )
    assert result["resolved"] is True
    assert result["best_source_offer"]["source_id"] == "b"
