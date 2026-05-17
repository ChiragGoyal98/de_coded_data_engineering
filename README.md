# personal-tele-project

A starter repo for a beginner-focused Data Engineering learning hub.

This project includes:
- `index.html` and `styles.css` for a static landing page
- `bot/telegram_post_bot.py` as a Telegram group posting bot skeleton
- `bot/README.md` with setup and free hosting recommendations
- `project-plan.md` with the full launch plan and content strategy

## Quick start
1. Open `index.html` and update the page title, copy, and Telegram group link.
2. Create a Telegram group and a bot via `@BotFather`.
3. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_GROUP_ID` and run `python bot/telegram_post_bot.py`.
4. Deploy the site to GitHub Pages, Cloudflare Pages, or Azure Static Web Apps for free.

## Free hosting options
- Website: GitHub Pages, Cloudflare Pages, Azure Static Web Apps
- Bot: Railway free tier, Replit, or Azure Functions using free credits

## Secret management
- Use environment variables for all bot tokens and group IDs.
- Copy `.env.example` to `.env` for local development.
- `.env` is ignored by Git via `.gitignore` and should never be committed.
- Deploy secrets to your host environment securely, not in code.

## Notes
Replace the placeholder Telegram group URL in `index.html` once your group is ready. Customize the bot content in `bot/telegram_post_bot.py` with your article summaries and links.

This repo contains the initial plan for a beginner-focused Data Engineering website and Telegram funnel.

- See `project-plan.md` for the recommended structure and MVP roadmap.
