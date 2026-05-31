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
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://chiraggoyal98.github.io/de_coded_data_engineering").strip().rstrip("/")

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
SITE_DIR = ROOT_DIR / "apps" / "web" / "public"
SITE_ARTICLES_DIR = SITE_DIR / "articles"
SITE_CONTENT_FILE = SITE_DIR / "content.json"
TOPICS_FILE = Path(__file__).resolve().parent / "topics.json"

NEWS_PROMPT = (
    "Provide a single-line catchy headline for a data engineering news brief. "
    "Then, on new lines, write a concise beginner-friendly summary. "
    "Include three bullet points covering: cloud platforms, AI/API tooling, and practical advice. "
    "Do not include dates or 'Dear Reader' intros."
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
        "Use standard Markdown for structure (## for headers, * for lists). "
        "Structure as: Introduction, Why it matters, Step-by-step walkthrough, Common mistakes, One practice task. "
        "Include one short code example when relevant."
    )


def build_summary(generated_text: str) -> str:
    # Strip markdown symbols for a clean summary
    clean_text = re.sub(r'[#*`_]', '', generated_text)
    paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
    if not paragraphs:
        return clean_text[:200].strip()
    
    # Skip meta-talk: all caps, short headers, or common LLM intros
    ignore_patterns = [r'^WELCOME TO', r'^DE-CODED', r'^HERE IS', r'^TITLE:', r'^INTRODUCTION']
    idx = 0
    while idx < len(paragraphs) and (paragraphs[idx].isupper() or len(paragraphs[idx]) < 60 or any(re.match(p, paragraphs[idx].upper()) for p in ignore_patterns)):
        idx += 1
    
    target = paragraphs[idx] if idx < len(paragraphs) else paragraphs[0]
    
    if len(target) > 240:
        target = target[:240].rsplit(" ", 1)[0] + "..."
    return target


def estimate_reading_time(text: str) -> int:
    words = len(text.split())
    return max(1, round(words / 200))


def build_article_url(slug: str) -> str:
    return f"articles/{slug}.html"


def build_article_full_link(slug: str) -> str:
    return f"{SITE_BASE_URL.rstrip('/')}/articles/{slug}.html"


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
        header_match = re.match(r'^(#{1,3})\s+(.*)', line)
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
    body_html = convert_markdown_to_html(generated_text)
    reading_time = estimate_reading_time(generated_text)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(topic)} | DE-Coded Lab</title>
  <meta name="description" content="{html.escape(summary)}" />
  <meta property="og:title" content="{html.escape(topic)}" />
  <meta property="og:description" content="{html.escape(summary)}" />
  <meta property="og:type" content="article" />
  <link rel="stylesheet" href="../styles.css" />
  <style>
    :root {{ --primary: #2563eb; --text: #1f2937; --light-bg: #f9fafb; }}
    body {{ line-height: 1.7; color: var(--text); font-family: Inter, system-ui, -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 0 1rem; }}
    .article-meta {{ color: #6b7280; font-size: 0.875rem; margin-bottom: 2rem; }}
    blockquote {{ border-left: 4px solid var(--primary); padding-left: 1rem; font-style: italic; color: #4b5563; margin: 1.5rem 0; }}
    .code-container {{ position: relative; margin: 2rem 0; border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden; }}
    .copy-button {{ 
      position: absolute; top: 0.5rem; right: 0.5rem; z-index: 10;
      padding: 0.4rem 0.8rem; font-size: 0.75rem; font-weight: 600;
      cursor: pointer; background: #ffffff; border: 1px solid #d1d5da; border-radius: 4px;
      transition: background-color 0.2s, box-shadow 0.2s;
    }}
    .copy-button:hover {{ background-color: #f3f4f6; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    pre {{ margin: 0 !important; padding: 1.2rem !important; background: #f6f8fa; overflow-x: auto; }}
  </style>
</head>
<body>
  <header class="hero hero-tight">
    <div class="container header-nav">
      <a class="site-brand" href="../index.html"><img class="logo-img" src="../logo.svg" alt="DE-Coded Lab logo" /><span>DE-Coded Lab</span></a>
      <nav class="site-nav">
        <a href="../index.html">Home</a>
        <a href="../news.html">News</a>
        <a href="../apis.html">API/SDK</a>
      </nav>
    </div>
  </header>
  <main class="container content-wrapper">
    <article class="article-page section-block">
      <nav class="breadcrumb"><a href="../index.html">Home</a> &raquo; {html.escape(category)}</nav>
      <h1>{html.escape(topic)}</h1>
      <div class="article-meta">
        <span>Published: {datetime.utcnow().strftime('%b %d, %Y')}</span> &bull; 
        <span>{reading_time} min read</span>
      </div>
      <p class="article-summary">{html.escape(summary)}</p>
      <hr />
      {body_html}
      <footer class="article-footer">
        <p><a class="link-button" href="../index.html">Explore more tutorials &rarr;</a></p>
      </footer>
    </article>
  </main>
  <script>
    function copyCode(button) {{
      const pre = button.nextElementSibling;
      const code = pre.querySelector('code');
      navigator.clipboard.writeText(code.innerText).then(() => {{
        button.textContent = 'Copied!';
        setTimeout(() => {{ button.textContent = 'Copy'; }}, 2000);
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


def save_article_page(topic: str, generated_text: str, summary: str) -> Path:
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
        
        # Extract headline (first non-empty line) and body
        news_lines = [l.strip() for l in news_text.split("\n") if l.strip()]
        headline = re.sub(r'[#*]', '', news_lines[0]) if news_lines else "Data Engineering Update"
        body_text = "\n".join(news_lines[1:]) if len(news_lines) > 1 else news_text
        
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
