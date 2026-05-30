# DE-Coded Lab

DE-Coded Lab is an automated data engineering content platform.
Every 8 hours it generates:
- one detailed article
- one news brief
- one Telegram update

## Repository structure
- `apps/web`: Astro website
- `apps/web/public/content.json`: generated feed used by homepage and news page
- `apps/web/public/articles`: generated article pages
- `pipeline`: LLM content generation scripts
- `bot`: Telegram posting scripts
- `.github/workflows/daily-content.yml`: scheduled automation every 8 hours

## Local development
1. Copy `.env.example` to `.env`.
2. Fill `GOOGLE_API_KEY`, `GOOGLE_API_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_GROUP_ID`, `SITE_BASE_URL`.
3. Generate fresh content:
   ```bash
   python pipeline/content_generator.py
   ```
4. Run Astro web app:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
5. Optional Telegram test:
   ```bash
   python bot/send_test_message.py
   ```

## Free hosting and deployment strategy
- Website hosting option A: GitHub Pages (fully free for static site).
- Website hosting option B: Cloudflare Pages free plan with custom domain.
- Automated generation: GitHub Actions cron (`0 */8 * * *`).
- Telegram traffic loop: bot script reads `apps/web/public/content.json`.
- Cost profile: domain purchase only at early stage.

## Notes
- Canonical web root is now `apps/web`.

