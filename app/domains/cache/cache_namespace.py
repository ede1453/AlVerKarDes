import os

DEFAULT_CACHE_NAMESPACE = "aici"


def get_cache_namespace() -> str:
    raw = os.getenv("AICI_CACHE_NAMESPACE", DEFAULT_CACHE_NAMESPACE).strip()
    if not raw:
        return DEFAULT_CACHE_NAMESPACE
    return normalize_cache_namespace(raw)


def normalize_cache_namespace(namespace: str) -> str:
    normalized = namespace.strip().lower()
    normalized = normalized.replace(" ", "-").replace("_", "-")

    allowed = []
    for char in normalized:
        if char.isalnum() or char in {"-", ":"}:
            allowed.append(char)

    cleaned = "".join(allowed).strip("-:")
    return cleaned or DEFAULT_CACHE_NAMESPACE


def build_namespaced_cache_key(key: str, namespace: str | None = None) -> str:
    namespace = normalize_cache_namespace(namespace or get_cache_namespace())
    key = str(key).strip()

    if key.startswith(f"{namespace}:"):
        return key

    return f"{namespace}:{key}"


def strip_cache_namespace(key: str, namespace: str | None = None) -> str:
    namespace = normalize_cache_namespace(namespace or get_cache_namespace())
    prefix = f"{namespace}:"

    if key.startswith(prefix):
        return key[len(prefix):]

    return key
