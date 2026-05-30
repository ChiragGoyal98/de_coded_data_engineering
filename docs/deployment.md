# Deployment (No-cost-first)

## Option A) GitHub Pages (free)
1. Push branch to GitHub.
2. Merge to `main`.
3. In repository settings, open `Pages`.
4. Set source to `GitHub Actions`.
5. Workflow `.github/workflows/deploy-github-pages.yml` will build and deploy `apps/web`.
6. Optional: attach custom domain in Pages settings.

## Option B) Cloudflare Pages (free)
1. Create a Cloudflare Pages project from this repository.
2. Build settings:
   - Framework: `Astro`
   - Root directory: `apps/web`
   - Build command: `npm run build`
   - Output directory: `dist`
3. Attach custom domain.

## CI and content automation
- Web CI workflow: `.github/workflows/web-ci.yml`
  - Runs build checks for app changes.
- Content generation workflow: `.github/workflows/daily-content.yml`
  - Runs every 8 hours.
  - Updates `apps/web/public/content.json` and `apps/web/public/articles/`.
  - Sends Telegram update after generation.

## Telegram loop
- Bot reads feed from `apps/web/public/content.json`.
- Posts latest article summary and latest news brief.

## Required secrets/variables
- `GOOGLE_API_KEY`
- `GOOGLE_API_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_GROUP_ID`
- `SITE_BASE_URL`

## GitHub secrets setup
In your repository:
1. Open `Settings` -> `Secrets and variables` -> `Actions`.
2. Add each secret above exactly as named.
3. Do not store secrets in committed files.
