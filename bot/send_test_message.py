import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID")

if not BOT_TOKEN or not GROUP_ID:
    raise SystemExit(
        "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_GROUP_ID.\n"
        "Copy .env.example to .env and add your values."
    )

message = "Test message: your Telegram group connection is working!"

import asyncio

async def send_test():
    try:
        async with Bot(token=BOT_TOKEN) as bot:
            result = await bot.send_message(chat_id=GROUP_ID, text=message)
            print("Message sent successfully.")
            print("Message ID:", result.message_id)
    except Exception as e:
        raise SystemExit(f"Failed to send message: {e}")

if __name__ == "__main__":
    asyncio.run(send_test())
