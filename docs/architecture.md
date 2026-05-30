# Architecture

## Goal
Build a weekend-maintainable content platform that:
- publishes data engineering content every 8 hours
- drives traffic through Telegram
- stays low-cost with static hosting

## Stack
- Frontend: Astro static site (`apps/web`)
- Content pipeline: Python + Gemini API (`pipeline`)
- Distribution: Telegram bot script (`bot`)
- Automation: GitHub Actions cron (`.github/workflows/daily-content.yml`)
- Hosting: Cloudflare Pages (free tier) + low-cost domain

## Content flow
1. GitHub Actions triggers every 8 hours.
2. `pipeline/content_generator.py` generates one new article and one news brief.
3. Files are written to `apps/web/public/articles` and `apps/web/public/content.json`.
4. Workflow commits updates.
5. Telegram bot reads the latest content feed and posts to group.

## Why static-first
- Fast page loads and good SEO baseline.
- Easy AdSense readiness.
- No paid app server needed for initial growth.
- Clear migration path to APIs/functions later if needed.
