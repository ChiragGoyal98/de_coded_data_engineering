# Pipeline

This pipeline generates the content feed that powers the website and Telegram channel.

## Outputs
- Markdown drafts: `pipeline/output/`
- Article pages: `apps/web/public/articles/`
- Feed file: `apps/web/public/content.json`

## Run
```bash
python pipeline/content_generator.py
```

## Environment variables
- `GOOGLE_API_KEY`
- `GOOGLE_API_URL`
- `SITE_BASE_URL`

## Notes
- Generator is scheduled by GitHub Actions every 8 hours.
- Output is intentionally static so it can be deployed on zero-cost hosting tiers.
