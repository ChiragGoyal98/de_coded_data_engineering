# Telegram Bot

This bot posts the latest generated article and brief to your Telegram group.

## Content source

`apps/web/public/content.json`

## Scripts

- `send_test_message.py` — posts once (used by GitHub Actions after each content run).
- `telegram_post_bot.py` — long-running bot with an 8-hour scheduler.

**Important:** GitHub Actions already posts via `send_test_message.py`. Do not run `telegram_post_bot.py` on a schedule in parallel or you will double-post.

## Run

```bash
python bot/send_test_message.py
```

One-off post from the long-running bot entrypoint:

```bash
python bot/telegram_post_bot.py --once
```

## Required variables

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_GROUP_ID`
- `SITE_BASE_URL` (must match GitHub Pages, e.g. `https://chiraggoyal98.github.io/de_coded_data_engineering`)
