# personal-tele-project

A starter repo for a beginner-focused Data Engineering learning hub.

This project includes:
- `site/` for the static website and brand assets
- `bot/telegram_post_bot.py` for daily Telegram group posting
- `pipeline/` for Google AI Studio content generation and website publishing
- `bot/README.md` with bot setup and hosting guidance
- `project-plan.md` with the launch plan and content strategy

## What is new
- Periodic content generation with the pipeline
- Website integration using `site/content.json` and generated article pages
- Telegram bot messages that link directly to the latest shared article
- Free hosting guidance for website and bot deployments

## Quick start
1. Copy `.env.example` to `.env` and add your values.
2. Set `GOOGLE_API_KEY`, `GOOGLE_API_URL`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_GROUP_ID`.
3. Set `SITE_BASE_URL` to your live website URL or preview URL.
4. Run the content generator:
   ```bash
   python pipeline/content_generator.py
   ```
5. Run the bot locally:
   ```bash
   python bot/telegram_post_bot.py
   ```
6. Deploy the website using a free static host and keep `site/content.json` synchronized.

## Free hosting options
- Website: Cloudflare Pages is easiest for the `site/` folder.
- Bot: Railway free tier or Replit are low-friction hosts for small Telegram bots.
- Automation: GitHub Actions can run the generator daily and commit new content.

## Automation
A scheduled workflow is included at `.github/workflows/daily-content.yml` to generate and commit fresh website content each day.

## Secret management
- Keep secrets in `.env` locally.
- Do not commit `.env`.
- Use GitHub Secrets or your hosting provider’s secret store for deployment.

## Notes
- The website homepage now loads `site/content.json` and displays the latest generated articles.
- The bot reads the same generated content so Telegram and the site stay aligned.
- Update the Telegram group link in `site/index.html` after your group is ready.
