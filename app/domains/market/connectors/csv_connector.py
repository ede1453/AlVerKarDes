import csv
from pathlib import Path

from app.domains.market.connectors.base import FeedConnector
from app.domains.market.connectors.schemas import FeedItem


class CSVFeedConnector(FeedConnector):
    name = "csv_feed"

    def parse(self, path: Path) -> list[FeedItem]:
        items = []
        with path.open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                items.append(
                    FeedItem(
                        store_slug=row["store_slug"],
                        product_title=row["product_title"],
                        product_url=row["product_url"],
                        price=float(row["price"]),
                        currency=row.get("currency") or "EUR",
                        original_price=float(row["original_price"]) if row.get("original_price") else None,
                        shipping_price=float(row["shipping_price"]) if row.get("shipping_price") else None,
                        stock_status=row.get("stock_status"),
                        brand=row.get("brand"),
                        gtin=row.get("gtin"),
                        sku=row.get("sku"),
                        metadata={"source_file": str(path)},
                    )
                )
        return items
