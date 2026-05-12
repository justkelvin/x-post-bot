from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

import asyncio
import httpx
import feedparser

from app.models import NewsItem

NEWS_DEDUPE_MULTIPLIER = 2


async def fetch_newsapi(topic: str, api_key: str, hours: int, limit: int) -> list[NewsItem]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "from": (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(),
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": limit,
        "apiKey": api_key,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    items: list[NewsItem] = []
    for article in articles:
        title = article.get("title") or "Untitled"
        description = article.get("description") or ""
        url_value = article.get("url") or ""
        source = (article.get("source") or {}).get("name") or "NewsAPI"
        items.append(NewsItem(title=title, description=description, url=url_value, source=source))
    return items


async def fetch_google_news_rss(topic: str, limit: int) -> list[NewsItem]:
    query = topic.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    loop = asyncio.get_event_loop()
    feed = await loop.run_in_executor(None, feedparser.parse, url)
    items: list[NewsItem] = []
    for entry in feed.entries[:limit]:
        title = getattr(entry, "title", "Untitled")
        description = getattr(entry, "summary", "")
        link = getattr(entry, "link", "")
        items.append(NewsItem(title=title, description=description, url=link, source="Google News"))
    return items


def _dedupe(items: Iterable[NewsItem]) -> list[NewsItem]:
    seen: set[str] = set()
    deduped: list[NewsItem] = []
    for item in items:
        key = item.url or item.title
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


async def gather_news(
    topic: str,
    *,
    use_newsapi: bool,
    news_api_key: str | None,
    news_api_hours: int,
    news_limit: int,
) -> list[NewsItem]:
    tasks = [fetch_google_news_rss(topic, news_limit)]
    if use_newsapi and news_api_key:
        tasks.append(fetch_newsapi(topic, news_api_key, news_api_hours, news_limit))
    results = await asyncio.gather(*tasks, return_exceptions=True)

    items: list[NewsItem] = []
    for result in results:
        if isinstance(result, Exception):
            continue
        items.extend(result)
    # Keep extra items to preserve variety after deduplication.
    return _dedupe(items)[: news_limit * NEWS_DEDUPE_MULTIPLIER]
