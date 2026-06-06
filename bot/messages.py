"""Shared Telegram message formatting for DE-Coded Lab."""

import html
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT_DIR / "pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from site_urls import (  # noqa: E402
    CANONICAL_SITE_BASE_URL,
    article_public_url,
    assert_canonical_article_url,
)

TELEGRAM_GROUP = "https://t.me/DE_Coded_Data_Engineering"


def resolve_article_url(post: dict) -> str:
    """Always use the canonical GitHub Pages URL (never trust secrets or full_url)."""
    path = (post.get("url") or "").lstrip("/")
    url = article_public_url(path) if path else f"{CANONICAL_SITE_BASE_URL}/"
    assert_canonical_article_url(url)
    return url


def _strip_markdown(text: str) -> str:
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", text or "")
    cleaned = re.sub(r"[*_`#]", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def telegram_summary(post: dict, max_length: int = 220) -> str:
    raw = (post.get("summary") or "").strip()
    text = _strip_markdown(raw)

    skip = (
        text.lower().startswith("welcome to"),
        text.lower().startswith("welcome back"),
        text.lower().startswith("de-coded lab:"),
        text.lower().startswith("here is a polished"),
        text.lower().startswith("title:"),
        len(text) < 50,
    )
    if any(skip) and raw:
        paragraphs = [_strip_markdown(p) for p in raw.split("\n") if p.strip()]
        text = next((p for p in paragraphs if len(p) >= 50 and not p.lower().startswith("welcome")), text)

    if len(text) > max_length:
        text = text[: max_length - 3].rsplit(" ", 1)[0] + "..."
    return text or "A new hands-on tutorial just dropped on DE-Coded Lab."


def _escape_telegram(text: str) -> str:
    return re.sub(r"([_\[\]`])", r"\\\1", text)


def build_message(post: dict, news_item=None, *, site_base_url: str = "") -> str:
    del site_base_url  # ignored — URLs are always canonical

    url = resolve_article_url(post)
    title = post.get("title", "New tutorial")
    category = post.get("category", "Data Engineering")
    summary = telegram_summary(post)
    
    # HTML escape dynamic values to prevent telegram HTML parsing errors
    safe_title = html.escape(title)
    safe_category = html.escape(category)
    safe_summary = html.escape(summary)

    msg = [
        f"🔥 <b>New on DE-Coded Lab</b> · <i>{safe_category}</i>",
        "",
        f"📘 <b>{safe_title}</b>",
        "",
        safe_summary,
        "",
        "💡 <i>Why open it?</i> Step-by-step walkthrough, one code example, and a practice task you can add to your portfolio.",
        "",
        "👉 <b>Read the full tutorial:</b>",
        url,
    ]

    if news_item and news_item.get("headline"):
        headline = _strip_markdown(news_item.get("headline", ""))
        if headline.lower().startswith("headline:"):
            headline = headline.split(":", 1)[1].strip()
        if len(headline) > 100:
            headline = headline[:97].rsplit(" ", 1)[0] + "..."
        msg.extend(["", f"📰 <b>Today's brief:</b> {html.escape(headline)}"])

    msg.extend(
        [
            "",
            f"🧠 More tutorials: <a href=\"{CANONICAL_SITE_BASE_URL}/\">DE-Coded Lab</a>",
            f"💬 Discuss & get updates: <a href=\"{TELEGRAM_GROUP}\">Telegram group</a>",
        ]
    )
    return "\n".join(msg)
