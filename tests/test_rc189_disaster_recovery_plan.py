from app.domains.deal_storage.reliability_governance import StorageReliabilityGovernanceService


def test_rc189_dr_plan_and_test():
    service = StorageReliabilityGovernanceService()

    plan = service.create_disaster_recovery_plan(
        plan_name="Primary DB recovery",
        rpo_minutes=15,
        rto_minutes=60,
        primary_region="eu-central-1",
        recovery_region="eu-west-1",
        steps=["promote replica", "validate data"],
    )["plan"]

    result = service.record_disaster_recovery_test(
        plan_id=plan["plan_id"],
        actual_rpo_minutes=10,
        actual_rto_minutes=45,
        successful=True,
        notes="Passed",
    )

    assert result["objectives_met"] is True
    assert result["plan"]["status"] == "VALIDATED"
