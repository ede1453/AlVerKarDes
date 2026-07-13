from app.domains.commerce_ingestion.operations import ConnectorOperationsService


def test_rc120_register_secret_reference():
    service = ConnectorOperationsService()
    result = service.register_credential_profile(
        profile_id="amazon-de-prod",
        provider="aws-secrets-manager",
        secret_reference="arn:aws:secretsmanager:eu-central-1:123:secret:aici/amazon",
    )
    assert result["registered"] is True
    assert result["profile"]["profile_id"] == "amazon-de-prod"

def test_rc120_inline_secret_rejected():
    service = ConnectorOperationsService()
    result = service.register_credential_profile(
        profile_id="bad",
        provider="inline",
        secret_reference="api_key=plain-text",
    )
    assert result["registered"] is False
    assert result["reason"] == "INLINE_SECRET_NOT_ALLOWED"
