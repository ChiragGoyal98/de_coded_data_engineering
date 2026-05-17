import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID")  # e.g. -1001234567890

DAILY_POSTS = [
    {
        "title": "Python for ETL Beginners",
        "summary": "Learn how to use Python scripts, file I/O, and pandas to build simple ETL flows.",
        "link": "https://yourdomain.com/python-etl"
    },
    {
        "title": "Azure Data Factory Pipeline Basics",
        "summary": "See how Azure Data Factory connects data sources, transforms data, and schedules jobs.",
        "link": "https://yourdomain.com/azure-data-factory"
    },
    {
        "title": "Start with Databricks Notebooks",
        "summary": "A beginner-friendly guide to creating and running your first Databricks notebook.",
        "link": "https://yourdomain.com/databricks-notebook"
    }
]

def build_message(post: dict) -> str:
    return (
        f"*{post['title']}*\n"
        f"{post['summary']}\n\n"
        f"Read more: {post['link']}\n"
        "\n" \
        "Join the community for daily updates and certification tips."
    )

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
            "Welcome! This bot posts daily data engineering summaries and links."
        )

async def post_daily_summary(app):
    if not GROUP_ID:
        logger.error("TELEGRAM_GROUP_ID is not set.")
        return

    bot = app.bot
    today = datetime.utcnow().weekday()
    post = DAILY_POSTS[today % len(DAILY_POSTS)]

    try:
        await bot.send_message(
            chat_id=GROUP_ID,
            text=build_message(post),
            parse_mode="Markdown"
        )
        logger.info("Posted daily summary to group %s", GROUP_ID)
    except TelegramError as error:
        logger.error("Failed to post daily summary: %s", error)

async def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        post_daily_summary,
        CronTrigger(hour=8, minute=0),
        args=[app],
        id="daily_summary"
    )
    scheduler.start()

    logger.info("Bot started. Waiting for updates and scheduled posts.")
    await app.start()
    await app.updater.start_polling()
    await app.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
