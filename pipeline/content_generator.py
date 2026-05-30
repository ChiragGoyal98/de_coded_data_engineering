import html
import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
GOOGLE_API_URL = os.getenv(
    "GOOGLE_API_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
).strip()
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://yourdomain.com").strip().rstrip("/")

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
SITE_DIR = Path(__file__).resolve().parent.parent / "site"
SITE_ARTICLES_DIR = SITE_DIR / "articles"
SITE_CONTENT_FILE = SITE_DIR / "content.json"

TOPIC_POOL = [
    {"category": "Programming Basics", "title": "Python OOP for Data Engineers"},
    {"category": "Programming Basics", "title": "SQL Window Functions with Real ETL Use Cases"},
    {"category": "Programming Basics", "title": "PySpark Transformations for Large Datasets"},
    {"category": "Azure", "title": "Azure Data Factory orchestration patterns"},
    {"category": "Azure", "title": "Azure Synapse Analytics fundamentals"},
    {"category": "Azure", "title": "Azure Data Lake design for analytics teams"},
    {"category": "Databricks", "title": "Databricks Delta Lake best practices"},
    {"category": "Databricks", "title": "Databricks notebook collaboration best practices"},
    {"category": "LLM APIs", "title": "Calling LLM APIs from Python with retries and fallbacks"},
    {"category": "LLM APIs", "title": "SDK patterns for production-grade AI integrations"},
]

NEWS_PROMPT = (
    "Write a concise beginner-friendly data engineering news brief. "
    "Focus on verified and generic trends without inventing product launches or dates. "
    "Include three bullets: cloud platforms, AI API tooling, and practical learner advice."
)
MAX_NEWS_ITEMS = 10
MAX_ARTICLES = 60

API_KEY = GOOGLE_API_KEY
API_URL = GOOGLE_API_URL


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ensure_site_dirs() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    SITE_ARTICLES_DIR.mkdir(parents=True, exist_ok=True)


def load_site_content():
    if not SITE_CONTENT_FILE.exists():
        return {"articles": [], "news": []}

    try:
        content = json.loads(SITE_CONTENT_FILE.read_text(encoding="utf-8"))
        if not isinstance(content, dict):
            return {"articles": [], "news": []}
        articles = content.get("articles")
        news = content.get("news")
        return {
            "articles": articles if isinstance(articles, list) else [],
            "news": news if isinstance(news, list) else [],
        }
    except Exception as err:
        print("Warning: failed to load existing site content:", err)
        return {"articles": [], "news": []}


def normalize_text(text: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2014": "-",
        "\u2013": "-",
        "\u2026": "...",
    }
    normalized = text
    for bad, good in replacements.items():
        normalized = normalized.replace(bad, good)
    return normalized


def slugify(value: str) -> str:
    lowered = value.lower().strip().replace("/", "-")
    sanitized = re.sub(r"[^a-z0-9\s-]", "", lowered)
    return "-".join(sanitized.split())


def build_prompt(category: str, topic: str) -> str:
    return (
        f"You are writing for a beginner-friendly technical blog titled 'DataFoundry Lab'. "
        f"Write a detailed tutorial article about '{topic}' under category '{category}'. "
        "Output plain text only and avoid markdown symbols like #, *, or bullets that start with markdown syntax. "
        "Structure as: Introduction, Why it matters, Step-by-step walkthrough, Common mistakes, One practice task. "
        "Include one short code example when relevant."
    )


def build_summary(generated_text: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in generated_text.split("\n\n") if paragraph.strip()]
    if not paragraphs:
        return generated_text.strip()
    summary = paragraphs[0]
    if len(summary) > 240:
        trimmed = summary[:240].rsplit(" ", 1)[0]
        return f"{trimmed}..."
    return summary


def build_article_url(slug: str) -> str:
    return f"articles/{slug}.html"


def build_article_full_link(slug: str) -> str:
    return f"{SITE_BASE_URL}/articles/{slug}.html"


def build_article_html(topic: str, generated_text: str, summary: str) -> str:
    paragraphs = [html.escape(paragraph.strip()) for paragraph in generated_text.split("\n\n") if paragraph.strip()]
    body_html = "\n".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(topic)} | DataFoundry Lab</title>
  <link rel="stylesheet" href="../styles.css" />
</head>
<body>
  <header class="hero hero-tight">
    <div class="container header-nav">
      <a class="site-brand" href="../index.html"><img class="logo-img" src="../logo.svg" alt="DataFoundry Lab logo" /><span>DataFoundry Lab</span></a>
      <nav class="site-nav">
        <a href="../index.html">Home</a>
        <a href="../news.html">News</a>
        <a href="../apis.html">API/SDK</a>
      </nav>
    </div>
  </header>
  <main class="container">
    <article class="article-page section-block">
      <p class="eyebrow">Generated Article</p>
      <h1>{html.escape(topic)}</h1>
      <p class="article-summary">{html.escape(summary)}</p>
      {body_html}
      <p><a class="link-button" href="../index.html">Back to home</a></p>
    </article>
  </main>
</body>
</html>
"""


def request_google_ai(prompt: str) -> dict:
    if not API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not set in the environment.")
    if not API_URL:
        raise RuntimeError("GOOGLE_API_URL is not set in the environment.")

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ]
    }
    request_data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_text = response.read().decode("utf-8")
            return json.loads(response_text)
    except urllib.error.HTTPError as err:
        error_text = err.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"API request failed with status {err.code}: {err.reason}\n{error_text}"
        ) from err
    except urllib.error.URLError as err:
        raise RuntimeError(f"API request failed: {err.reason}") from err


def parse_google_response(result: dict) -> str:
    if not isinstance(result, dict):
        raise ValueError("Unexpected Google response format: expected a JSON object.")

    candidates = result.get("candidates")
    if isinstance(candidates, list) and candidates:
        texts = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content")
            if isinstance(content, dict):
                parts = content.get("parts")
                if isinstance(parts, list):
                    for part in parts:
                        if isinstance(part, dict) and "text" in part:
                            texts.append(str(part["text"]))
        if texts:
            return "\n\n".join(texts)

    output = result.get("output")
    if isinstance(output, str):
        return output
    if isinstance(output, list):
        return "\n\n".join(str(item) for item in output)

    raise ValueError("Unexpected Google response format. Update parser logic.")


def save_article(topic: str, content: str) -> Path:
    ensure_output_dir()
    file_name = f"{slugify(topic)}.md"
    file_path = OUTPUT_DIR / file_name
    file_path.write_text(content, encoding="utf-8")
    return file_path


def save_article_page(topic: str, generated_text: str, summary: str) -> Path:
    ensure_site_dirs()
    slug = slugify(topic)
    file_path = SITE_ARTICLES_DIR / f"{slug}.html"
    file_path.write_text(build_article_html(topic, generated_text, summary), encoding="utf-8")
    return file_path


def save_site_content(content_items, news_items) -> Path:
    ensure_site_dirs()
    content_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "articles": content_items,
        "news": news_items,
    }
    SITE_CONTENT_FILE.write_text(
        json.dumps(content_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return SITE_CONTENT_FILE


def format_markdown(topic: str, generated_text: str) -> str:
    return (
        f"# {topic}\n\n"
        f"{generated_text.strip()}\n\n"
        "---\n"
        "*Generated with Google AI Studio integration.*\n"
    )


def pick_next_topic(existing_articles):
    existing_slugs = {
        slugify(item.get("title", ""))
        for item in existing_articles
        if isinstance(item, dict)
    }
    for entry in TOPIC_POOL:
        if slugify(entry["title"]) not in existing_slugs:
            return entry
    index = datetime.utcnow().hour % len(TOPIC_POOL)
    return TOPIC_POOL[index]


def main() -> None:
    existing = load_site_content()
    existing_articles = existing.get("articles", [])
    existing_news = existing.get("news", [])

    next_topic = pick_next_topic(existing_articles)
    topic = next_topic["title"]
    category = next_topic["category"]
    print(f"Generating content for: {topic} ({category})")

    generated_text = normalize_text(parse_google_response(request_google_ai(build_prompt(category, topic))))
    summary = build_summary(generated_text)

    saved_path = save_article(topic, format_markdown(topic, generated_text))
    print(f"Saved markdown: {saved_path}")
    page_path = save_article_page(topic, generated_text, summary)
    print(f"Saved website article: {page_path}")

    slug = slugify(topic)
    article_data = {
        "title": topic,
        "category": category,
        "summary": summary,
        "url": build_article_url(slug),
        "full_url": build_article_full_link(slug),
        "published": datetime.utcnow().isoformat() + "Z",
    }

    articles = [article_data]
    for article in existing_articles:
        if isinstance(article, dict) and slugify(article.get("title", "")) != slug:
            articles.append(article)
    articles = articles[:MAX_ARTICLES]

    cycle_stamp = datetime.utcnow().strftime("%Y-%m-%dT%H")
    news = list(existing_news)
    if not any(isinstance(item, dict) and item.get("published_cycle") == cycle_stamp for item in news):
        print("Generating a fresh news update for this cycle.")
        news_text = normalize_text(parse_google_response(request_google_ai(NEWS_PROMPT)))
        news.insert(
            0,
            {
                "headline": build_summary(news_text),
                "body": news_text,
                "published": datetime.utcnow().isoformat() + "Z",
                "published_cycle": cycle_stamp,
            },
        )
    news = news[:MAX_NEWS_ITEMS]

    content_path = save_site_content(articles, news)
    print(f"Saved website metadata: {content_path}")


if __name__ == "__main__":
    main()
