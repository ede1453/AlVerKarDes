import re


class BasicProductPageExtractor:
    def extract(self, *, content: str | None, url: str):
        if not content:
            return {}

        title_match = re.search(r"<h1>(.*?)</h1>", content, re.IGNORECASE | re.DOTALL)
        price_match = re.search(r"class=['\"]price['\"]>(.*?)<", content, re.IGNORECASE | re.DOTALL)
        currency_match = re.search(r"class=['\"]currency['\"]>(.*?)<", content, re.IGNORECASE | re.DOTALL)

        return {
            "url": url,
            "product_name": self._clean(title_match.group(1)) if title_match else None,
            "price": self._clean(price_match.group(1)) if price_match else None,
            "currency": self._clean(currency_match.group(1)) if currency_match else None,
            "extractor": "basic_product_page_v1",
        }

    def _clean(self, value: str):
        return " ".join(value.strip().split())
