# Telegram Group Bot Setup

This folder contains a simple Telegram bot skeleton for posting daily article summaries to your Telegram group.

## What this does
- posts one summary to the Telegram group every day at 08:00 UTC
- provides a `/start` command for the bot
- uses environment variables for configuration

## Requirements
- Python 3.11+ recommended
- `python-telegram-bot` and `APScheduler`

Install dependencies:

```bash
pip install python-telegram-bot apscheduler
```

## Setup
1. Create a bot with `@BotFather` on Telegram.
2. Create your Telegram group and add the bot as an administrator.
3. Get the group chat ID. Send `/start` in the group after the bot is added, and it will reply with the chat ID.
4. Set environment variables.

For local development, copy `.env.example` to `.env` and fill in your values.

```bash
cp .env.example .env
# then edit .env and add your actual values
```

Or set them directly in your shell:

```bash
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_GROUP_ID="-1001234567890"
```

On Windows PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN = "your-bot-token"
$env:TELEGRAM_GROUP_ID = "-1001234567890"
```

## Run the bot locally

```bash
python bot/telegram_post_bot.py
```

## Free hosting options
- [Railway](https://railway.app): free tier supports small bots with a simple deployment.
- [Replit](https://replit.com): quick hosting for proof-of-concept bots.
- [Azure Functions](https://azure.microsoft.com/free): free credits can host a webhook bot if you want Azure experience.

## Next steps
- customize `DAILY_POSTS` with your own article summaries and links
- update the site link placeholders in `index.html`
- use LinkedIn to share the Telegram group and your certification prep resources
