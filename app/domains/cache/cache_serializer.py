def _isoformat_or_none(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def serialize_cache_entry(entry):
    if isinstance(entry, dict):
        return {
            "key": entry.get("key"),
            "value": entry.get("value"),
            "ttl_seconds": entry.get("ttl_seconds"),
            "created_at": _isoformat_or_none(entry.get("created_at")),
            "expires_at": _isoformat_or_none(entry.get("expires_at")),
        }

    return {
        "key": entry.key,
        "value": entry.value,
        "ttl_seconds": entry.ttl_seconds,
        "created_at": entry.created_at.isoformat(),
        "expires_at": entry.expires_at.isoformat(),
    }


def serialize_cache_lookup(result, key=None):
    if result is None:
        return {
            "hit": False,
            "key": key,
            "value": None,
            "metadata": {"reason": "CACHE_MISS"},
        }

    if isinstance(result, dict):
        return {
            "hit": True,
            "key": result.get("key", key),
            "value": result.get("value"),
            "metadata": result.get("metadata", {}),
        }

    return {
        "hit": result.hit,
        "key": result.key,
        "value": result.value,
        "metadata": result.metadata,
    }


def serialize_cache_status(status):
    if isinstance(status, dict):
        return {
            "enabled": status.get("enabled", True),
            "backend": status.get("backend"),
            "entry_count": status.get("entry_count", 0),
            "hit_count": status.get("hit_count", 0),
            "miss_count": status.get("miss_count", 0),
            "hit_rate": status.get("hit_rate", 0.0),
            "miss_rate": status.get("miss_rate", 0.0),
            "metadata": status.get("metadata", {}),
        }

    return {
        "enabled": status.enabled,
        "backend": status.backend,
        "entry_count": status.entry_count,
        "hit_count": status.hit_count,
        "miss_count": status.miss_count,
        "hit_rate": status.hit_rate,
        "miss_rate": status.miss_rate,
        "metadata": status.metadata,
    }