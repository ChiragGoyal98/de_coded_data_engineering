import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram import Bot

ROOT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT_DIR / "pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from messages import build_message
from site_urls import canonical_site_base_url

load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID")
SITE_BASE_URL = canonical_site_base_url(os.environ.get("SITE_BASE_URL"))
CONTENT_JSON_PATH = Path(__file__).resolve().parent.parent / "apps" / "web" / "public" / "content.json"

if not BOT_TOKEN or not GROUP_ID:
    raise SystemExit(
        "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_GROUP_ID.\n"
        "Copy .env.example to .env and add your values."
    )


def load_site_content():
    if not CONTENT_JSON_PATH.exists():
        return None
    try:
        with CONTENT_JSON_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as err:
        print(f"Warning: Failed to load content: {err}")
        return None


def find_today_news(news_items):
    if not isinstance(news_items, list):
        return None
    from datetime import datetime

    today = datetime.utcnow().date().isoformat()
    for item in news_items:
        if isinstance(item, dict) and item.get("published", "").startswith(today):
            return item
    return news_items[0] if news_items else None


async def send_test():
    content = load_site_content()
    if not content or not content.get("articles"):
        print("No content available. Run the generator first.")
        return

    post = content["articles"][0]
    news_item = find_today_news(content.get("news", []))
    message = build_message(post, news_item)

    try:
        async with Bot(token=BOT_TOKEN) as bot:
            result = await bot.send_message(
                chat_id=GROUP_ID,
                text=message,
                parse_mode="HTML",
            )
            print("Test message sent successfully.")
            print(f"Message ID: {result.message_id}")
            print(f"Article: {post['title']}")
            print(f"News included: {'Yes' if news_item else 'No'}")
    except Exception as err:
        raise SystemExit(f"Failed to send message: {err}") from err


if __name__ == "__main__":
    asyncio.run(send_test())
