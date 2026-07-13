def serialize_crawl_result(result):
    return {
        "crawl_id": result.crawl_id,
        "url": result.url,
        "connector": result.connector,
        "status": result.status,
        "allowed": result.allowed,
        "content_type": result.content_type,
        "content": result.content,
        "extracted": result.extracted,
        "warnings": result.warnings,
        "metadata": result.metadata,
        "created_at": result.created_at.isoformat(),
    }
