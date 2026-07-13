def serialize_lowest_price_report(report):
    return {
        "current_amount": str(report.current_amount) if report.current_amount is not None else None,
        "lowest_7d": _serialize_point(report.lowest_7d),
        "lowest_30d": _serialize_point(report.lowest_30d),
        "lowest_90d": _serialize_point(report.lowest_90d),
        "lowest_all_time": _serialize_point(report.lowest_all_time),
    }


def _serialize_point(point):
    return {
        "amount": str(point.amount) if point.amount is not None else None,
        "observed_at": point.observed_at.isoformat() if point.observed_at else None,
        "window_days": point.window_days,
        "label": point.label,
    }
