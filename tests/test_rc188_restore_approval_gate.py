from app.domains.deal_storage.reliability_governance import StorageReliabilityGovernanceService


def test_rc188_restore_approval():
    service = StorageReliabilityGovernanceService()

    request = service.request_restore_approval(
        backup_id="backup-1",
        requested_by="operator",
        environment="production",
        reason="Disaster recovery",
    )["approval"]

    before = service.can_execute_restore(
        approval_id=request["approval_id"]
    )
    assert before["allowed"] is False

    decision = service.decide_restore_approval(
        approval_id=request["approval_id"],
        approved=True,
        decided_by="admin",
        decision_reason="Approved",
    )
    assert decision["approval"]["status"] == "APPROVED"

    after = service.can_execute_restore(
        approval_id=request["approval_id"]
    )
    assert after["allowed"] is True
