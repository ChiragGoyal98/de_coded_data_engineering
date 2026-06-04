import html
import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from site_urls import article_public_url, canonical_site_base_url, site_href

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
GOOGLE_API_URL = os.getenv(
    "GOOGLE_API_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent",
).strip()
SITE_BASE_URL = canonical_site_base_url(os.getenv("SITE_BASE_URL"))

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
SITE_DIR = ROOT_DIR / "apps" / "web" / "public"
SITE_ARTICLES_DIR = SITE_DIR / "articles"
SITE_CONTENT_FILE = SITE_DIR / "content.json"
TOPICS_FILE = ROOT_DIR / "topics.json"
PLACEHOLDER_HOSTS = ("yourdomain.com", "example.com")

NEWS_PROMPT = (
    "Write a beginner-friendly data engineering news brief.\n"
    "First line must be: HEADLINE: <short title, max 12 words, plain text only>\n"
    "Then exactly three bullet lines:\n"
    "- Cloud: <one sentence>\n"
    "- AI: <one sentence>\n"
    "- Tip: <one sentence>\n"
    "No markdown symbols, no dates, no introductions."
)
MAX_NEWS_ITEMS = 10
MAX_ARTICLES = 60

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
        f"You are writing for a beginner-friendly technical blog titled 'DE-Coded Lab'. "
        f"Write a detailed tutorial article about '{topic}' under category '{category}'. "
        "Use standard Markdown (## and ### for headers, - for bullet lists). "
        "Do NOT repeat the article title as a heading. Do NOT write 'Welcome to DE-Coded Lab' or similar intros. "
        "Do not use ** in the opening paragraph. "
        "Structure as: Introduction, Why it matters, Step-by-step walkthrough, Common mistakes, One practice task. "
        "Include one short code example when relevant."
    )


def clean_generated_article_text(topic: str, text: str) -> str:
    topic_pattern = re.compile(re.escape(topic), re.IGNORECASE)
    cleaned_lines = []
    seen_intro = False

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append(line)
            continue

        if re.match(r"^\*{3,}$", stripped):
            continue

        if re.match(r"^#{1,6}\s+", stripped) and topic_pattern.search(stripped):
            continue

        lower = stripped.lower()
        if not seen_intro and (
            lower.startswith("welcome to de-coded")
            or lower.startswith("welcome back to de-coded")
            or lower.startswith("title:")
            or (lower.startswith("# ") and "de-coded" in lower)
        ):
            seen_intro = True
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def strip_markdown_inline(text: str) -> str:
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    cleaned = re.sub(r"[*_`#]", "", cleaned)
    return cleaned.strip()


def build_summary(generated_text: str) -> str:
    clean_text = strip_markdown_inline(generated_text)
    paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
    if not paragraphs:
        return clean_text[:200].strip()

    ignore_patterns = [
        r"^WELCOME TO",
        r"^WELCOME BACK",
        r"^DE-CODED",
        r"^HERE IS",
        r"^TITLE:",
        r"^INTRODUCTION",
        r"^CATEGORY:",
    ]
    idx = 0
    while idx < len(paragraphs) and (
        paragraphs[idx].isupper()
        or len(paragraphs[idx]) < 60
        or any(re.match(p, paragraphs[idx].upper()) for p in ignore_patterns)
    ):
        idx += 1

    target = paragraphs[idx] if idx < len(paragraphs) else paragraphs[0]

    if len(target) > 240:
        target = target[:240].rsplit(" ", 1)[0] + "..."
    return target


def parse_news_response(news_text: str) -> tuple:
    lines = [line.strip() for line in news_text.split("\n") if line.strip()]
    headline = "Data engineering update"
    body_lines = []

    for line in lines:
        if line.upper().startswith("HEADLINE:"):
            headline = strip_markdown_inline(line.split(":", 1)[1])[:120]
            continue
        body_lines.append(line)

    if headline == "Data engineering update" and lines:
        headline = strip_markdown_inline(lines[0])[:120]
        body_lines = lines[1:]

    body_text = "\n".join(body_lines) if body_lines else news_text
    return headline, body_text


def estimate_reading_time(text: str) -> int:
    words = len(text.split())
    return max(1, round(words / 200))


def build_article_url(slug: str) -> str:
    return f"articles/{slug}.html"


def build_article_full_link(slug: str) -> str:
    return article_public_url(build_article_url(slug))


def slug_from_article_url(url: str) -> str:
    path = (url or "").strip()
    if path.startswith("articles/"):
        path = path[len("articles/") :]
    if path.endswith(".html"):
        path = path[: -len(".html")]
    return path


def normalize_article_entry(article: dict) -> dict:
    if not isinstance(article, dict):
        return article

    title = article.get("title", "")
    url = article.get("url", "")
    slug = slug_from_article_url(url) if url else slugify(title)
    article["url"] = build_article_url(slug)

    article["full_url"] = build_article_full_link(slug)
    return article


def normalize_articles(articles: list) -> list:
    return [normalize_article_entry(item) for item in articles if isinstance(item, dict)]


def convert_markdown_to_html(text: str) -> str:
    """Basic markdown to HTML converter for headers, bold, and lists."""
    lines = text.split("\n")
    html_output = []
    in_list = False
    in_code_block = False

    def process_inline(text: str) -> str:
        content = html.escape(text)
        content = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', content)
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'_(.*?)_', r'<em>\1</em>', content)
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
        content = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', content)
        return content

    for line in lines:
        # Preserve indentation for code blocks, but strip for logic
        stripped = line.lstrip()

        # Handle Code Blocks
        if stripped.startswith("```"):
            if in_code_block:
                html_output.append("</code></pre></div>")
                in_code_block = False
            else:
                lang = stripped.replace("```", "").strip()
                html_output.append(f'<div class="code-container"><button class="copy-button" onclick="copyCode(this)">Copy</button><pre><code class="language-{lang}">')
                in_code_block = True
            continue
        
        if in_code_block:
            html_output.append(html.escape(line))
            continue

        line = stripped
        if not line:
            if in_list:
                html_output.append("</ul>")
                in_list = False
            continue

        # Headers
        header_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if header_match:
            if in_list: html_output.append("</ul>"); in_list = False
            level = len(header_match.group(1))
            html_output.append(f"<h{level}>{process_inline(header_match.group(2))}</h{level}>")
        # Blockquotes
        elif line.startswith("> "):
            if in_list: html_output.append("</ul>"); in_list = False
            html_output.append(f"<blockquote>{process_inline(line[2:])}</blockquote>")
        # Horizontal Rules
        elif re.match(r'^---+$', line):
            if in_list: html_output.append("</ul>"); in_list = False
            html_output.append("<hr />")
        # Lists
        elif re.match(r'^[\*\-\+]\s+', line) or re.match(r'^\d+\.\s+', line):
            if not in_list:
                html_output.append("<ul>")
                in_list = True
            # Strip the bullet/number
            content = re.sub(r'^([\*\-\+]|\d+\.)\s+', '', line)
            html_output.append(f"<li>{process_inline(content)}</li>")
        # Paragraphs
        else:
            if in_list:
                html_output.append("</ul>")
                in_list = False
            html_output.append(f"<p>{process_inline(line)}</p>")

    if in_list:
        html_output.append("</ul>")
    return "\n".join(html_output)


def build_article_html(topic: str, category: str, generated_text: str, summary: str) -> str:
    cleaned_text = clean_generated_article_text(topic, generated_text)
    body_html = convert_markdown_to_html(cleaned_text)
    reading_time = estimate_reading_time(cleaned_text)
    clean_summary = strip_markdown_inline(build_summary(cleaned_text))
    home = site_href("index.html")
    news = site_href("news/index.html")
    apis = site_href("apis/index.html")
    logo = site_href("logo.svg")
    styles = site_href("styles.css")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(topic)} | DE-Coded Lab</title>
  <meta name="description" content="{html.escape(clean_summary)}" />
  <meta property="og:title" content="{html.escape(topic)}" />
  <meta property="og:description" content="{html.escape(clean_summary)}" />
  <meta property="og:type" content="article" />
  <link rel="stylesheet" href="{styles}" />
</head>
<body>
  <header class="hero hero-tight">
    <div class="container header-nav">
      <a class="site-brand" href="{home}"><img class="logo-img" src="{logo}" alt="DE-Coded Lab logo" /><span>DE-Coded Lab</span></a>
      <nav class="site-nav">
        <a href="{home}">Home</a>
        <a href="{news}">News</a>
        <a href="{apis}">APIs</a>
      </nav>
    </div>
  </header>
  <main class="container">
    <article class="article-page section-block article-prose">
      <nav class="breadcrumb"><a href="{home}">Home</a> &raquo; <span>{html.escape(category)}</span></nav>
      <p class="pill">{html.escape(category)}</p>
      <h1>{html.escape(topic)}</h1>
      <div class="article-meta">
        <span>Published: {datetime.utcnow().strftime('%b %d, %Y')}</span>
        <span aria-hidden="true">&bull;</span>
        <span>{reading_time} min read</span>
      </div>
      <p class="article-lead">{html.escape(clean_summary)}</p>
      <div class="article-body">
      {body_html}
      </div>
      <footer class="article-footer">
        <a class="link-button" href="{home}">Explore more tutorials &rarr;</a>
      </footer>
    </article>
  </main>
  <footer class="footer">
    <p>DE-Coded Lab — practical data engineering tutorials.</p>
  </footer>
  <script>
    function copyCode(button) {{
      const pre = button.nextElementSibling;
      const code = pre && pre.querySelector("code");
      if (!code) return;
      navigator.clipboard.writeText(code.innerText).then(() => {{
        button.textContent = "Copied!";
        setTimeout(() => {{ button.textContent = "Copy"; }}, 2000);
      }});
    }}
  </script>
</body>
</html>
"""


def request_google_ai(prompt: str) -> dict:
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not set in the environment.")
    if not GOOGLE_API_URL:
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
        GOOGLE_API_URL,
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GOOGLE_API_KEY,
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


def save_article_page(topic: str, category: str, generated_text: str, summary: str) -> Path:
    ensure_site_dirs()
    slug = slugify(topic)
    file_path = SITE_ARTICLES_DIR / f"{slug}.html"
    file_path.write_text(build_article_html(topic, category, generated_text, summary), encoding="utf-8")
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
    
    topic_pool = []
    if TOPICS_FILE.exists():
        topic_pool = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
    
    for entry in topic_pool:
        if slugify(entry["title"]) not in existing_slugs:
            return entry
    
    index = datetime.utcnow().hour % len(topic_pool) if topic_pool else 0
    return topic_pool[index] if topic_pool else {"category": "General", "title": "Data Engineering"}


def main() -> None:
    existing = load_site_content()
    existing_articles = normalize_articles(existing.get("articles", []))
    existing_news = existing.get("news", [])

    next_topic = pick_next_topic(existing_articles)
    topic = next_topic["title"]
    category = next_topic["category"]
    print(f"Generating content for: {topic} ({category})")

    generated_text = normalize_text(parse_google_response(request_google_ai(build_prompt(category, topic))))
    generated_text = clean_generated_article_text(topic, generated_text)
    summary = build_summary(generated_text)

    saved_path = save_article(topic, format_markdown(topic, generated_text))
    print(f"Saved markdown: {saved_path}")
    page_path = save_article_page(topic, category, generated_text, summary)
    print(f"Saved website article: {page_path}")

    slug = slugify(topic)
    article_data = {
        "title": topic,
        "category": category,
        "summary": summary,
        "url": build_article_url(slug),
        "full_url": build_article_full_link(slug),
        "published": datetime.utcnow().isoformat() + "Z",
        "is_new": True
    }

    articles = [article_data]
    for article in existing_articles:
        article["is_new"] = False
        if isinstance(article, dict) and slugify(article.get("title", "")) != slug:
            articles.append(article)
    articles = articles[:MAX_ARTICLES]

    cycle_stamp = datetime.utcnow().strftime("%Y-%m-%dT%H")
    news = list(existing_news)
    if not any(isinstance(item, dict) and item.get("published_cycle") == cycle_stamp for item in news):
        print("Generating a fresh news update for this cycle.")
        news_text = normalize_text(parse_google_response(request_google_ai(NEWS_PROMPT)))
        headline, body_text = parse_news_response(news_text)
        
        news.insert(
            0,
            {
                "headline": headline,
                "body": convert_markdown_to_html(body_text),
                "published": datetime.utcnow().isoformat() + "Z",
                "published_cycle": cycle_stamp,
                "is_new": True
            },
        )
    
    for i, item in enumerate(news):
        if i > 0: item["is_new"] = False
        
    news = news[:MAX_NEWS_ITEMS]

    content_path = save_site_content(articles, news)
    print(f"Saved website metadata: {content_path}")


if __name__ == "__main__":
    main()
