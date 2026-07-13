def serialize_price_point(point):
    return {
        "id": point.id,
        "product_key": point.product_key,
        "marketplace": point.marketplace,
        "price": str(point.price),
        "currency": point.currency,
        "observed_at": point.observed_at.isoformat(),
        "metadata": point.metadata,
    }


def serialize_price_history_summary(summary):
    return {
        "product_key": summary.product_key,
        "currency": summary.currency,
        "point_count": summary.point_count,
        "min_price": None if summary.min_price is None else str(summary.min_price),
        "max_price": None if summary.max_price is None else str(summary.max_price),
        "average_price": None if summary.average_price is None else str(summary.average_price.quantize(summary.latest_price) if summary.latest_price is not None else summary.average_price),
        "latest_price": None if summary.latest_price is None else str(summary.latest_price),
        "trend": summary.trend,
        "points": [serialize_price_point(point) for point in summary.points],
    }
