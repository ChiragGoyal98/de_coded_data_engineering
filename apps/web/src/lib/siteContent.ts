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

export function stripHtml(value: string): string {
  return value.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

export function cleanHeadline(value: string): string {
  return stripHtml(value.replace(/^[#*\s]+/, "").replace(/\*\*/g, "")).slice(0, 200);
}

export function newsPreview(body: string, maxLength = 400): string {
  const plain = stripHtml(body);
  if (plain.length <= maxLength) {
    return plain;
  }
  return `${plain.slice(0, maxLength).trim()}...`;
}

export function articleSearchText(article: Article): string {
  return [article.title, article.category, article.summary]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}
