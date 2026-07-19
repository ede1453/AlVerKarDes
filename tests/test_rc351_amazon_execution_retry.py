from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc351_execution_retry():
    calls=[]
    def transport(**kwargs):
        calls.append(1)
        if len(calls)==1:
            return {"status_code":429,"json":{}}
        return {"status_code":200,"json":{"items":[]}}
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret",maximum_retries=1,fixture_mode=True),http_transport=transport,sleep=lambda _:None)
    r=s.execute(operation="x",method="POST",path="/x",payload={})
    assert r["attempt_count"]==2
