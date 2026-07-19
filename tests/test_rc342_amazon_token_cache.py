from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc342_token_cache():
    calls=[]
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"),token_fetcher=lambda a,b:(calls.append(1) or {"access_token":"abc","expires_in":3600}))
    assert s.get_access_token()["cached"] is False
    assert s.get_access_token()["cached"] is True
    assert len(calls)==1
