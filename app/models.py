from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class NewsItem:
    title: str
    description: str
    url: str
    source: str


class TweetRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)
    num_tweets: int = Field(3, ge=1, le=10)
    style_override: str | None = Field(default=None, max_length=1000)
    persona_override: str | None = Field(default=None, max_length=500)
    viral_guide_override: str | None = Field(default=None, max_length=2000)
    avoid_override: str | None = Field(default=None, max_length=500)
    use_newsapi: bool = True


class TweetResponse(BaseModel):
    topic: str
    tweets: list[str]
    sources: list[str]
    used_news_count: int


class ScheduleRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)
    interval_minutes: int | None = Field(default=None, ge=5, le=1440)
    num_tweets: int = Field(3, ge=1, le=10)


class ScheduleResponse(BaseModel):
    job_id: str
    interval_minutes: int
    topic: str


def news_to_bullets(items: Iterable[NewsItem]) -> str:
    bullets = []
    for item in items:
        line = f"- {item.title}"
        if item.description:
            line += f" ({item.description})"
        bullets.append(line)
    return "\n".join(bullets) if bullets else "- No real-time sources found."
