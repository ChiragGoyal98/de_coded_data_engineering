"""Shared Telegram message formatting for DE-Coded Lab."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT_DIR / "pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from site_urls import CANONICAL_SITE_BASE_URL, article_public_url, canonical_site_base_url  # noqa: E402

SITE_BASE_URL = CANONICAL_SITE_BASE_URL


def resolve_article_url(post: dict, site_base_url: str) -> str:
    base = canonical_site_base_url(site_base_url)
    path = (post.get("url") or "").lstrip("/")
    if path:
        return article_public_url(base, path)
    return f"{base}/"


def build_message(post: dict, news_item=None, *, site_base_url: str = SITE_BASE_URL) -> str:
    url = resolve_article_url(post, site_base_url)
    title = post.get("title", "New Article")
    category = post.get("category", "Data Engineering")
    summary = (post.get("summary") or "").strip()

    msg = [
        "🚀 *New Tutorial Published!*",
        "━━━━━━━━━━━━━━",
        f"📘 *Topic:* {title}",
        f"🏷 *Category:* {category}",
        "",
        f"📝 {summary}",
        "",
        "🔗 *Read the full guide here:*",
        url,
        "",
        "━━━━━━━━━━━━━━",
    ]

    if news_item and news_item.get("headline"):
        headline = news_item["headline"].strip().lstrip("#").strip()
        msg.append(f"📰 *News:* {headline}")
        msg.append("")

    site = canonical_site_base_url(site_base_url)
    msg.append(f"👉 Visit [DE-Coded Lab]({site}/)")
    return "\n".join(msg)
