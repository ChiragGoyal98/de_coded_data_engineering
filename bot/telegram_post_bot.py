import json
import logging
import os
import sys
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from telegram.error import TelegramError
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = ROOT_DIR / "pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from messages import build_message
from site_urls import canonical_site_base_url

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID")
SITE_BASE_URL = canonical_site_base_url(os.environ.get("SITE_BASE_URL"))
CONTENT_JSON_PATH = Path(__file__).resolve().parent.parent / "apps" / "web" / "public" / "content.json"

FALLBACK_POSTS = [
    {
        "title": "Python OOP for Data Engineers",
        "category": "Programming Basics",
        "summary": "Use classes and composition to make ETL pipelines easier to maintain.",
        "url": "articles/python-oop-for-data-engineers.html",
    },
    {
        "title": "Azure Data Factory orchestration patterns",
        "category": "Azure",
        "summary": "Design clean parent-child pipelines and resilient retries for production.",
        "url": "articles/azure-data-factory-orchestration-patterns.html",
    },
]


def load_site_content():
    if not CONTENT_JSON_PATH.exists():
        logger.warning("Site content file not found: %s", CONTENT_JSON_PATH)
        return None
    try:
        with CONTENT_JSON_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data
    except Exception as error:
        logger.error("Failed to load site content: %s", error)
    return None


async def start_command(update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    chat_type = update.message.chat.type
    if chat_type != "private":
        await update.message.reply_text(
            f"This group chat ID is: {chat_id}\n\nUse this value as TELEGRAM_GROUP_ID in your .env file."
        )
        logger.info("Detected group chat ID: %s", chat_id)
    else:
        await update.message.reply_text(
            "Welcome! This bot posts fresh data engineering content every 8 hours."
        )


async def post_summary(app):
    if not GROUP_ID:
        logger.error("TELEGRAM_GROUP_ID is not set.")
        return

    content = load_site_content()
    post = FALLBACK_POSTS[0]
    news_item = None

    if isinstance(content, dict):
        articles = content.get("articles", [])
        if isinstance(articles, list) and articles:
            post = articles[0]
        news_items = content.get("news", [])
        if isinstance(news_items, list) and news_items:
            news_item = news_items[0]

    try:
        await app.bot.send_message(
            chat_id=GROUP_ID,
            text=build_message(post, news_item),
            parse_mode="Markdown",
        )
        logger.info("Posted summary to group %s", GROUP_ID)
    except TelegramError as error:
        logger.error("Failed to post summary: %s", error)


async def on_startup(app: Application):
    if "--once" in sys.argv:
        await post_summary(app)
        logger.info("Posted once via --once flag. Exiting without scheduler.")
        return

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        post_summary,
        CronTrigger(hour="*/8", minute=0),
        args=[app],
        id="summary_every_8_hours",
    )
    scheduler.start()
    app.bot_data["scheduler"] = scheduler
    logger.info("Scheduler started for 8-hour posting cycle.")


async def on_shutdown(app: Application):
    scheduler = app.bot_data.get("scheduler")
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set.")
        return

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )
    app.add_handler(CommandHandler("start", start_command))
    logger.info("Bot started. Use --once for a single post; otherwise waits for scheduled posts.")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
