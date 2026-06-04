"""Canonical public site URLs for DE-Coded Lab (GitHub Pages)."""

from typing import Optional
from urllib.parse import urlparse

CANONICAL_SITE_BASE_URL = "https://chiraggoyal98.github.io/de_coded_data_engineering"
SITE_PATH_PREFIX = "/de_coded_data_engineering"


def canonical_site_base_url(url: Optional[str] = None) -> str:
    """Return the GitHub Pages base URL, correcting common secret typos."""
    candidate = (url or "").strip().rstrip("/")
    if not candidate:
        return CANONICAL_SITE_BASE_URL

    parsed = urlparse(candidate)
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").rstrip("/")

    if host == "chiraggoyal98.github.io" and path == SITE_PATH_PREFIX:
        return f"https://{host}{path}"

    return CANONICAL_SITE_BASE_URL


def site_href(relative_path: str) -> str:
    """Build a root-relative path under the GitHub Pages base."""
    clean = relative_path.lstrip("/")
    return f"{SITE_PATH_PREFIX}/{clean}" if clean else f"{SITE_PATH_PREFIX}/"


def article_public_url(article_path: str) -> str:
    """Build a fully qualified article URL from `articles/<slug>.html`."""
    base = CANONICAL_SITE_BASE_URL.rstrip("/")
    path = (article_path or "").lstrip("/")
    if not path:
        return f"{base}/"
    return f"{base}/{path}"


def assert_canonical_article_url(url: str) -> None:
    if "decodeddataengineering" in url.lower():
        raise ValueError(f"Invalid article URL (bad path segment): {url}")
    if "/de_coded_data_engineering/" not in url:
        raise ValueError(f"Invalid article URL (missing site prefix): {url}")
