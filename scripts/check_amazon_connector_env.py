import os

required = [
    "AMAZON_CREATORS_BASE_URL",
    "AMAZON_CREATORS_MARKETPLACE",
    "AMAZON_CREATORS_PARTNER_TAG",
    "AMAZON_CREATORS_CLIENT_ID",
    "AMAZON_CREATORS_CLIENT_SECRET",
]

missing = [
    key
    for key in required
    if not os.getenv(key)
]

placeholders = [
    key
    for key in required
    if "CHANGE_ME" in os.getenv(key, "")
    or "REPLACE_WITH" in os.getenv(key, "")
]

if missing or placeholders:
    raise SystemExit(
        f"Amazon connector environment invalid. "
        f"Missing={missing}; placeholders={placeholders}"
    )

base_url = os.environ[
    "AMAZON_CREATORS_BASE_URL"
]

if not base_url.startswith("https://"):
    raise SystemExit(
        "AMAZON_CREATORS_BASE_URL must use HTTPS."
    )

print("Amazon connector environment check passed.")
