import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export interface Article {
  title: string;
  category?: string;
  summary?: string;
  url?: string;
  full_url?: string;
  published?: string;
  is_new?: boolean;
}

export interface NewsItem {
  headline?: string;
  body?: string;
  published?: string;
  published_cycle?: string;
  is_new?: boolean;
}

export interface SiteContent {
  generated_at?: string;
  articles: Article[];
  news: NewsItem[];
}

const contentPath = path.join(
  fileURLToPath(new URL(".", import.meta.url)),
  "../../public/content.json",
);

export function loadSiteContent(): SiteContent {
  if (!existsSync(contentPath)) {
    return { articles: [], news: [] };
  }

  try {
    const data = JSON.parse(readFileSync(contentPath, "utf-8"));
    return {
      generated_at: data.generated_at,
      articles: Array.isArray(data.articles) ? data.articles : [],
      news: Array.isArray(data.news) ? data.news : [],
    };
  } catch {
    return { articles: [], news: [] };
  }
}

export function articleHref(base: string, article: Article): string {
  if (article.url) {
    return `${base}${article.url}`;
  }
  return article.full_url || base;
}

export function decodeHtmlEntities(value: string): string {
  return value
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

export function stripMarkdown(value: string): string {
  return decodeHtmlEntities(value)
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/^[-*+]\s+/gm, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^---+$/gm, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function stripHtml(value: string): string {
  return stripMarkdown(value.replace(/<[^>]+>/g, " "));
}

export function deriveNewsHeadline(item: NewsItem): string {
  const plain = stripHtml(item.headline || "");
  const dateLabel = formatPublishedDate(item.published);

  if (!plain) {
    return dateLabel ? `Briefing · ${dateLabel}` : "Data engineering briefing";
  }

  if (/^here is a concise brief/i.test(plain)) {
    return dateLabel ? `Briefing · ${dateLabel}` : "Data engineering briefing";
  }
  if (/^data engineering brief/i.test(plain)) {
    return "Industry trends briefing";
  }
  if (/the data stream/i.test(plain)) {
    return "Azure and Databricks update";
  }

  const labelMatch = plain.match(/^([A-Za-z][A-Za-z0-9 /&-]{2,48}):/);
  if (labelMatch) {
    return labelMatch[1].trim();
  }

  const firstSentence = plain.split(/(?<=[.!?])\s+/)[0] || plain;
  if (firstSentence.length <= 90) {
    return firstSentence;
  }

  if (dateLabel) {
    return `Briefing · ${dateLabel}`;
  }

  return plain.split(/\s+/).slice(0, 8).join(" ");
}

export function prepareNewsBodyHtml(body: string): string {
  if (!body.trim()) {
    return "";
  }

  const isHtml = /<[a-z][\s\S]*>/i.test(body);
  let html = isHtml ? decodeHtmlEntities(body) : "";

  if (!isHtml) {
    const lines = body.split("\n").map((line) => line.trim()).filter(Boolean);
    const items: string[] = [];
    const paragraphs: string[] = [];

    for (const line of lines) {
      const bullet = line.match(/^[-*+]\s+(.*)$/);
      if (bullet) {
        items.push(`<li>${stripMarkdown(bullet[1])}</li>`);
        continue;
      }
      paragraphs.push(`<p>${stripMarkdown(line)}</p>`);
    }

    if (items.length) {
      html = `<ul>${items.join("")}</ul>`;
    }
    if (paragraphs.length) {
      html = `${html}${paragraphs.join("")}`;
    }
    if (!html) {
      html = `<p>${stripMarkdown(body)}</p>`;
    }
  } else {
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*\*/g, "");
  }

  return html;
}

export function cleanArticleSummary(summary?: string): string {
  if (!summary) {
    return "No summary available.";
  }

  const lines = summary
    .split("\n")
    .map((line) => stripMarkdown(line))
    .filter(Boolean);

  const skip = (text: string) =>
    /^welcome to/i.test(text) ||
    /^de-coded lab:/i.test(text) ||
    /^here is a polished/i.test(text) ||
    /^title:/i.test(text) ||
    /^category:/i.test(text) ||
    text.length < 40;

  const candidate = lines.find((line) => !skip(line)) || stripMarkdown(summary);

  if (candidate.length > 240) {
    return `${candidate.slice(0, 237).trim()}...`;
  }

  return candidate || "No summary available.";
}

export function formatPublishedDate(value?: string): string | null {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function articleSearchText(article: Article): string {
  return [article.title, article.category, cleanArticleSummary(article.summary)]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}
