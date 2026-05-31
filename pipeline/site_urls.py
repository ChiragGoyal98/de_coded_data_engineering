"""Canonical public site URLs for DE-Coded Lab (GitHub Pages)."""

from typing import Optional
from urllib.parse import urlparse

CANONICAL_SITE_BASE_URL = "https://chiraggoyal98.github.io/de_coded_data_engineering"


def canonical_site_base_url(url: Optional[str] = None) -> str:
    """Return the GitHub Pages base URL, correcting common secret typos."""
    candidate = (url or "").strip().rstrip("/")
    if not candidate:
        return CANONICAL_SITE_BASE_URL

    parsed = urlparse(candidate)
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").rstrip("/")

    if host == "chiraggoyal98.github.io" and path == "/de_coded_data_engineering":
        return f"https://{host}{path}"

    return CANONICAL_SITE_BASE_URL


def article_public_url(base_url: str, article_path: str) -> str:
    """Build a fully qualified article URL from `articles/<slug>.html`."""
    base = canonical_site_base_url(base_url).rstrip("/")
    path = (article_path or "").lstrip("/")
    if not path:
        return f"{base}/"
    return f"{base}/{path}"
