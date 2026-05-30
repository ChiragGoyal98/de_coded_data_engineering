# Pipeline

This folder contains a sample pipeline for generating data engineering content using Google AI Studio.

## Purpose

- Generate daily content summaries and article drafts
- Write generated output into `pipeline/output/`
- Provide a reusable bridge between the website and the Telegram bot

## Setup

1. Copy `.env.example` to `.env`
2. Add your `GOOGLE_API_KEY`, `GOOGLE_API_URL`, and optionally `GOOGLE_MODEL`
3. Install dependencies if needed:
   ```bash
   pip install python-dotenv
   ```
4. Run the sample generator:
   ```bash
   python pipeline/content_generator.py
   ```

## Google AI Studio setup

Google AI Studio may provide a free-tier quota. Confirm your account and free credits on the Google Cloud console.

### Create credentials

1. Sign into Google AI Studio or Google Cloud.
2. Create an API key in the Cloud console and enable the Generative AI API.
3. Copy `.env.example` to `.env`.
4. Set your variables:
   ```bash
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent
   ```
5. If Google changes its endpoint or request format, update `GOOGLE_API_URL` and the payload in `pipeline/content_generator.py`.

## Test Google AI connectivity

Use `python pipeline/test_google_ai_setup.py` to verify your key, endpoint, and account access before generating full content.

## Notes

- Google AI Studio free-tier quotas are subject to change; check your Google Cloud usage.
- If the API format changes, update `GOOGLE_API_URL` and the payload in `pipeline/content_generator.py`.
- This pipeline is intentionally simple so it can be extended into the website or bot workflows later.
