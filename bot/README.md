# Telegram Bot

This bot posts the latest generated article and brief to your Telegram group every 8 hours.

## Content source
`apps/web/public/content.json`

## Run
```bash
python bot/telegram_post_bot.py
```

## Test one message
```bash
python bot/send_test_message.py
```

## Required variables
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_GROUP_ID`
- `SITE_BASE_URL`
