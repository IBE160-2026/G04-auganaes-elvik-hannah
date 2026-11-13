"""Which push-service addresses the server may POST to (Story 3.2, SSRF, review of Story 3.1).

A subscription's endpoint comes from the client, and the job sends to it from the server, so an
endpoint such as `https://169.254.169.254/` would make the server call an internal address. Real
browsers only ever hand out the push services below, so an allowlist is enough, needs no DNS and
is tested offline. A new push service is one line here.
"""

from urllib.parse import urlsplit

# Exact hosts: Chrome and Edge on Android (FCM), Firefox, Safari.
ALLOWED_HOSTS: frozenset[str] = frozenset(
    {"fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com"}
)
# Whole domains (any subdomain): Windows notification service (Edge), Firefox's regional hosts.
ALLOWED_SUFFIXES: tuple[str, ...] = (
    ".notify.windows.com",
    ".push.services.mozilla.com",
    ".push.apple.com",
)


def is_allowed_endpoint(endpoint: str) -> bool:
    """True for an https address on a known push service, on the default port, with no login."""
    try:
        parts = urlsplit(endpoint)
        port = parts.port
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or parts.username is not None or port not in (None, 443):
        return False
    return host in ALLOWED_HOSTS or host.endswith(ALLOWED_SUFFIXES)
