# Telegram Group Bot Setup

This folder contains a Telegram bot that posts daily data engineering content to your group.

## What this does
- posts one article summary to the Telegram group every day at 08:00 UTC
- loads generated website content from `site/content.json`
- shares a website link and short summary when content is published
- provides a `/start` helper command for setup

## Requirements
- Python 3.11+ recommended
- `python-telegram-bot` and `APScheduler`

Install dependencies:

```bash
pip install python-telegram-bot apscheduler python-dotenv
```

## Setup
1. Create a bot with `@BotFather` on Telegram.
2. Create your Telegram group and add the bot as an administrator.
3. Get the group chat ID. Send `/start` in the group after the bot is added, and it will reply with the chat ID.
4. Copy `.env.example` to `.env` and fill in your values.

```bash
cp .env.example .env
# edit .env and add your actual values
```

Required variables:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_GROUP_ID`
- `SITE_BASE_URL` (optional, used to create full article links)

On Windows PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN = "your-bot-token"
$env:TELEGRAM_GROUP_ID = "-1001234567890"
$env:SITE_BASE_URL = "https://yourdomain.com"
```

## Run the bot locally

```bash
python bot/telegram_post_bot.py
```

## How it works
- The bot reads generated articles from `site/content.json`
- It posts the current article for the day with a website link
- If no generated content exists yet, it falls back to sample summary posts

## Free hosting options
- `Railway` free tier works well for Python bots
- `Replit` can host a small bot with your existing code
- `Azure Functions` is a good choice if you want cloud-hosted Python

## Next steps
- run `python pipeline/content_generator.py` to generate article pages and site metadata
- configure a scheduled workflow to generate new articles automatically each day
- update `site/index.html` and `SITE_BASE_URL` as your site goes live
