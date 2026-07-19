from app.domains.amazon_connector.service import AmazonCreatorsConfig, AmazonCreatorsConnectorService


def test_rc344_search_request():
    s=AmazonCreatorsConnectorService(AmazonCreatorsConfig(base_url="https://api.example",marketplace="amazon.de",partner_tag="tag",client_id="id",client_secret="secret"))
    r=s.build_search_request(keywords="laptop",page_size=100)
    assert r["pageSize"]==50
    assert r["marketplace"]=="amazon.de"
