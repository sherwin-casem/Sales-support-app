"""URL and domain normalization utilities."""

from urllib.parse import urlparse


def normalize_domain(url: str | None) -> str | None:
    if not url or not url.strip():
        return None
    raw = url.strip()
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    try:
        parsed = urlparse(raw)
        host = (parsed.netloc or parsed.path).lower()
        if host.startswith("www."):
            host = host[4:]
        return host or None
    except ValueError:
        return None


def normalize_website(url: str | None) -> str | None:
    if not url or not url.strip():
        return None
    raw = url.strip()
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    return raw
