"""
RSS Feed Fetcher for Current Affairs
======================================
Fetches and parses articles from Pakistani news RSS feeds:
  - dawn.com/feed
  - geo.tv/rss/1/0
  - app.com.pk/feed

Each article is normalised into a dict ready for relevance scoring.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

import httpx
import feedparser

logger = logging.getLogger(__name__)

# ── Feed Registry ────────────────────────────────────────────
RSS_FEEDS: list[dict[str, str]] = [
    {
        "name": "dawn",
        "url": "https://www.dawn.com/feed",
        "label": "Dawn News",
    },
    {
        "name": "geo",
        "url": "https://www.geo.tv/rss/1/0",
        "label": "Geo News",
    },
    {
        "name": "app",
        "url": "https://www.app.com.pk/feed",
        "label": "APP (Associated Press of Pakistan)",
    },
]

# Max articles per feed per run (avoid flooding)
MAX_ARTICLES_PER_FEED = 50

# HTTP timeout (some .pk sites are slow)
HTTP_TIMEOUT = 30.0


@dataclass
class RawArticle:
    """Normalised article from an RSS feed."""

    headline: str
    summary: str
    content: str
    source_name: str
    source_url: str
    published_date: date | None = None
    raw_categories: list[str] = field(default_factory=list)


def _parse_pub_date(entry: dict[str, Any]) -> date | None:
    """Extract publication date from a feedparser entry."""
    pub_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if pub_parsed:
        try:
            return datetime(*pub_parsed[:6], tzinfo=timezone.utc).date()
        except (TypeError, ValueError):
            pass

    # Fallback: try ISO string
    for key in ("published", "updated"):
        raw = entry.get(key, "")
        if raw:
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
            except ValueError:
                continue
    return None


def _extract_content(entry: dict[str, Any]) -> str:
    """Extract the best available content text from a feed entry."""
    # feedparser puts full content in entry.content[0].value
    if "content" in entry:
        for block in entry["content"]:
            val = block.get("value", "").strip()
            if val:
                return _strip_html(val)

    # Fallback to summary / description
    summary = entry.get("summary", "") or entry.get("description", "")
    return _strip_html(summary)


def _strip_html(text: str) -> str:
    """Naïve HTML tag stripping (no external dep)."""
    import re

    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


async def fetch_single_feed(feed_cfg: dict[str, str]) -> list[RawArticle]:
    """Fetch and parse a single RSS feed, returning normalised articles."""
    name = feed_cfg["name"]
    url = feed_cfg["url"]
    articles: list[RawArticle] = []

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "PPSCCrack-Bot/1.0"})
            resp.raise_for_status()
            raw_xml = resp.text

        parsed = feedparser.parse(raw_xml)

        if parsed.bozo and not parsed.entries:
            logger.warning("Feed %s returned malformed XML: %s", name, parsed.bozo_exception)
            return []

        for entry in parsed.entries[:MAX_ARTICLES_PER_FEED]:
            headline = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()

            if not headline or not link:
                continue

            content_text = _extract_content(entry)
            summary_text = _strip_html(entry.get("summary", "") or "")

            # Some entries are just a headline — skip ultra-short ones
            if len(content_text) < 30 and len(summary_text) < 30:
                continue

            raw_cats = [
                t.get("term", "").strip().lower()
                for t in entry.get("tags", [])
                if t.get("term")
            ]

            articles.append(
                RawArticle(
                    headline=headline[:500],
                    summary=summary_text[:2000] if summary_text else headline,
                    content=content_text[:10_000] if content_text else summary_text[:10_000],
                    source_name=name,
                    source_url=link[:500],
                    published_date=_parse_pub_date(entry),
                    raw_categories=raw_cats,
                )
            )

        logger.info("Fetched %d articles from %s (%s)", len(articles), name, url)

    except httpx.HTTPError as exc:
        logger.error("HTTP error fetching %s: %s", name, exc)
    except Exception as exc:
        logger.exception("Unexpected error fetching %s: %s", name, exc)

    return articles


async def fetch_all_feeds() -> list[RawArticle]:
    """Fetch all configured RSS feeds and return a combined list of articles."""
    all_articles: list[RawArticle] = []

    for feed_cfg in RSS_FEEDS:
        articles = await fetch_single_feed(feed_cfg)
        all_articles.extend(articles)

    logger.info("Total articles fetched from all feeds: %d", len(all_articles))
    return all_articles
