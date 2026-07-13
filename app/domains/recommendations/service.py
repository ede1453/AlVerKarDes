from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.agents.fraud_agent import FraudAgent, FraudInput
from app.domains.ai.agents.price_intelligence_agent import PriceIntelligenceAgent, PriceIntelligenceInput
from app.domains.ai.agents.product_research_agent import ProductResearchAgent
from app.domains.ai.agents.review_analyst_agent import ReviewAnalystAgent, ReviewInput
from app.domains.market.service import MarketService
from app.domains.products.normalization.schemas import ProductNormalizationInput
from app.domains.products.normalization.service import ProductNormalizationService
from app.domains.recommendations.decision_orchestrator import DecisionInput, DecisionOrchestrator
from app.domains.recommendations.repository import RecommendationRepository


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.market_service = MarketService(db)
        self.recommendation_repo = RecommendationRepository(db)
        self.product_research_agent = ProductResearchAgent(ProductNormalizationService())
        self.price_intelligence_agent = PriceIntelligenceAgent()
        self.review_analyst_agent = ReviewAnalystAgent()
        self.fraud_agent = FraudAgent()
        self.orchestrator = DecisionOrchestrator()

    async def analyze(self, *, product_url: str | None, product_name: str | None, offer_id: UUID | None, user_context: dict):
        session = await self.recommendation_repo.create_session(
            query_text=product_name,
            input_url=product_url,
            metadata={"offer_id": str(offer_id) if offer_id else None, "user_context_keys": list(user_context.keys())},
        )

        product_result = await self.product_research_agent.run(
            ProductNormalizationInput(product_url=product_url, product_name=product_name, country=user_context.get("country", "DE"), language=user_context.get("language", "en"))
        )

        if not offer_id:
            response = self._insufficient(product_result, "No offer_id was provided.", session.id)
            saved = await self.recommendation_repo.save_recommendation(session_id=session.id, decision=response["decision"], confidence=response["confidence"], summary=response["summary"], payload=response)
            response["recommendation_id"] = str(saved.id)
            return response

        current = await self.market_service.get_latest_price_point(offer_id)
        history = await self.market_service.get_price_points_for_offer(offer_id)

        if not current or len(history) < 5:
            response = self._insufficient(product_result, "Not enough stored price history for this offer.", session.id)
            saved = await self.recommendation_repo.save_recommendation(session_id=session.id, decision=response["decision"], confidence=response["confidence"], summary=response["summary"], payload=response)
            response["recommendation_id"] = str(saved.id)
            return response

        price_result = self.price_intelligence_agent.run(PriceIntelligenceInput(current_price=current, price_history=history))
        review_result = self.review_analyst_agent.run(ReviewInput(reviews=user_context.get("reviews", []), source_name=user_context.get("review_source")))

        historical_avg = price_result.evidence[0].get("data", {}).get("historical_average") if price_result.evidence else None
        fraud_result = self.fraud_agent.run(
            FraudInput(
                offer_url=product_url or user_context.get("offer_url", ""),
                current_price=current.amount,
                historical_avg_price=historical_avg,
                store_name=user_context.get("store_name"),
                store_trust_score=user_context.get("store_trust_score"),
            )
        )

        decision = self.orchestrator.decide(
            DecisionInput(
                product_confidence=product_result.confidence,
                price_signal=price_result.price_signal,
                price_confidence=price_result.confidence,
                review_confidence=review_result.confidence,
                review_reliability=review_result.review_reliability,
                fraud_risk_level=fraud_result.risk_level,
                fraud_score=fraud_result.risk_score,
            )
        )

        evidence = []
        evidence.extend(price_result.evidence)
        evidence.extend(review_result.evidence)
        evidence.append({"type": "FRAUD_ANALYSIS", "title": "Fraud risk analysis", "data": {"risk_level": fraud_result.risk_level, "risk_score": fraud_result.risk_score, "flags": fraud_result.flags}, "confidence": fraud_result.confidence})

        response = {
            "session_id": str(session.id),
            "decision": decision.decision,
            "confidence": decision.confidence,
            "summary": self._summary(product_result, price_result, review_result, fraud_result, decision),
            "reasons": decision.reasons,
            "evidence": evidence,
            "alternatives": [],
            "uncertainty": decision.uncertainty,
            "affiliate_disclosure": {"contains_affiliate_links": False, "explanation": "No affiliate links are used in this MVP decision flow."},
            "agent_trace": {
                "product_research": {"confidence": product_result.confidence, "uncertainty": product_result.uncertainty},
                "price_intelligence": {"discount_quality": price_result.discount_quality, "price_signal": price_result.price_signal, "confidence": price_result.confidence, "uncertainty": price_result.uncertainty},
                "review_analyst": {"review_reliability": review_result.review_reliability, "confidence": review_result.confidence, "uncertainty": review_result.uncertainty},
                "fraud_agent": {"risk_level": fraud_result.risk_level, "risk_score": fraud_result.risk_score, "flags": fraud_result.flags, "uncertainty": fraud_result.uncertainty},
            },
        }
        saved = await self.recommendation_repo.save_recommendation(session_id=session.id, decision=response["decision"], confidence=response["confidence"], summary=response["summary"], payload=response)
        response["recommendation_id"] = str(saved.id)
        return response

    def _insufficient(self, product_result, reason: str, session_id) -> dict:
        return {
            "session_id": str(session_id),
            "decision": "INSUFFICIENT_DATA",
            "confidence": min(product_result.confidence, 40),
            "summary": reason,
            "reasons": [{"type": "INSUFFICIENT_DATA", "title": "Insufficient data", "description": reason, "weight": -1}],
            "evidence": [],
            "alternatives": [],
            "uncertainty": {"level": "HIGH", "explanation": reason},
            "affiliate_disclosure": {"contains_affiliate_links": False, "explanation": "No affiliate links are used in this MVP decision flow."},
            "agent_trace": {"product_research": {"confidence": product_result.confidence, "uncertainty": product_result.uncertainty}},
        }

    def _summary(self, product_result, price_result, review_result, fraud_result, decision) -> str:
        identity = product_result.identity
        product_name = " ".join(p for p in [identity.brand, identity.product_family, identity.model] if p) or "the product"
        return f"For {product_name}, final decision is {decision.decision}. Price signal: {price_result.price_signal}. Review reliability: {review_result.review_reliability}. Fraud risk: {fraud_result.risk_level}."
