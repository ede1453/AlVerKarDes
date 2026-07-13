def serialize_price_statistics_report(report, trend_by_window: dict | None = None):
    trend_by_window = trend_by_window or {}

    return {
        "generated_at": report.generated_at.isoformat(),
        "windows": {
            label: {
                **_serialize_stats(stats),
                "trend": _serialize_trend(trend_by_window.get(label)),
            }
            for label, stats in report.windows.items()
        },
    }


def _serialize_stats(stats):
    return {
        "label": stats.label,
        "window_days": stats.window_days,
        "count": stats.count,
        "min_amount": _decimal_to_string(stats.min_amount),
        "max_amount": _decimal_to_string(stats.max_amount),
        "average_amount": _decimal_to_string(stats.average_amount),
        "median_amount": _decimal_to_string(stats.median_amount),
        "first_amount": _decimal_to_string(stats.first_amount),
        "last_amount": _decimal_to_string(stats.last_amount),
    }


def _serialize_trend(trend):
    if trend is None:
        return None

    return {
        "direction": trend.direction,
        "change_amount": _decimal_to_string(trend.change_amount),
        "change_percent": _decimal_to_string(trend.change_percent),
        "confidence": trend.confidence,
        "reason": trend.reason,
    }


def _decimal_to_string(value):
    if value is None:
        return None
    return str(value)
