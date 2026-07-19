from app.domains.amazon_connector.factory import build_amazon_connector

connector = build_amazon_connector()
result = connector.run_collection(
    keywords="laptop",
    page_size=10,
)

print(
    {
        "executed": result["executed"],
        "item_count": result["item_count"],
        "snapshot_count": result["snapshot_count"],
        "connector": result["connector"],
    }
)
