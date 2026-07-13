from app.domains.crawler.extractor import BasicProductPageExtractor


def test_basic_product_page_extractor_extracts_product_fields():
    extracted = BasicProductPageExtractor().extract(
        url="mock://product",
        content="<h1>MacBook Air</h1><span class='price'>949.00</span><span class='currency'>EUR</span>",
    )

    assert extracted["product_name"] == "MacBook Air"
    assert extracted["price"] == "949.00"
    assert extracted["currency"] == "EUR"
