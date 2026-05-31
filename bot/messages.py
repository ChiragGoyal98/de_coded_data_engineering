"""Shared Telegram message formatting for DE-Coded Lab."""

SITE_BASE_URL = "https://chiraggoyal98.github.io/de_coded_data_engineering"


def resolve_article_url(post: dict, site_base_url: str) -> str:
    base = (site_base_url or SITE_BASE_URL).strip().rstrip("/")
    full_url = post.get("full_url", "")
    if base and full_url and base.lower() in full_url.lower():
        return full_url
    path = (post.get("url") or "").lstrip("/")
    if path:
        return f"{base}/{path}"
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

    site = site_base_url.strip().rstrip("/") or SITE_BASE_URL
    msg.append(f"👉 Visit [DE-Coded Lab]({site}/)")
    return "\n".join(msg)
