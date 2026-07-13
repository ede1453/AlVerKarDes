import pytest

from app.domains.connectors.manual_connector import ManualConnector
from app.domains.connectors.sdk import ConnectorProductResult
from app.domains.decision.contract import DecisionContract, DecisionSignal
from app.domains.evidence.schemas import EvidenceBundle, EvidenceItem
from app.domains.products.canonical_service import CanonicalProductService


@pytest.mark.asyncio
async def test_manual_connector_search():
    connector = ManualConnector([
        ConnectorProductResult(
            source="manual",
            title="Apple MacBook Air M5 16GB 512GB",
            price=849,
            currency="EUR",
            confidence=95,
        )
    ])

    results = await connector.search("MacBook")
    assert len(results) == 1
    assert results[0].price == 849


def test_evidence_bundle():
    bundle = EvidenceBundle()
    bundle.add(EvidenceItem(
        type="PRICE_HISTORY",
        title="Lowest price detected",
        confidence=90,
        data={"current": 849, "lowest": 849},
    ))

    assert len(bundle.by_type("PRICE_HISTORY")) == 1


def test_decision_contract():
    decision = DecisionContract(
        decision="BUY",
        confidence=82,
        positive_signals=[
            DecisionSignal(
                type="PRICE",
                title="Strong price",
                description="Current price is near historical low.",
                weight=0.8,
                confidence=88,
            )
        ],
        what_could_change_my_decision=["A lower price from a trusted store."],
        uncertainty={"level": "LOW"},
        affiliate_disclosure={"contains_affiliate_links": False},
    )

    assert decision.decision == "BUY"
    assert decision.confidence == 82


def test_canonical_product_match():
    service = CanonicalProductService()

    left = service.build_match("Apple MacBook Air M5 16GB 512GB")
    right = service.build_match("Apple MacBook Air M5 16 GB 512 GB")

    assert left.confidence >= 90
    assert right.confidence >= 90
    assert left.canonical_key == right.canonical_key
