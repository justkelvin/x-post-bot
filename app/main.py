from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException

from app.config import DEFAULT_CONFIG, settings
from app.humanize import humanize_tweet
from app.llm import LLMError, chat_completion
from app.models import (
    ScheduleRequest,
    ScheduleResponse,
    TWEET_MAX_LENGTH,
    TweetRequest,
    TweetResponse,
    news_to_bullets,
)
from app.news import gather_news
from app.scheduler import scheduler
from app.storage import init_db, save_run

SYSTEM_TEMPLATE = """You are a master X (Twitter) ghostwriter with a unique voice.

{persona}

Your WRITING STYLE:
{writing_style}

Your VIRALITY GUIDE (mandatory rules):
{viral_guide}

WHAT TO AVOID:
{avoid}

Use the REAL-TIME INFORMATION below to craft tweets that feel immediate and human.
---
REAL-TIME CONTEXT:
{news_summaries}
"""

USER_TEMPLATE = """Write {num_tweets} distinct viral tweets about the topic: "{topic}".

Each tweet must:
- Obey the Virality Guide exactly.
- Sound like a real person, not a bot (vary sentence length, use everyday language, include a personal opinion).
- Incorporate at least one specific detail from the real-time context above.
- Be under 280 characters (strict).

Return them as a JSON array of strings, like: ["tweet1", "tweet2"]"""

ELLIPSIS = "…"

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db(settings.database_path)
    if settings.scheduler_enabled:
        scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()


app = FastAPI(title="x-post-bot", version="0.1.0", lifespan=lifespan)


def _build_config(req: TweetRequest) -> dict[str, str]:
    config = dict(DEFAULT_CONFIG)
    if req.style_override:
        config["writing_style"] = req.style_override
    if req.persona_override:
        config["persona"] = req.persona_override
    if req.viral_guide_override:
        config["viral_guide"] = req.viral_guide_override
    if req.avoid_override:
        config["avoid"] = req.avoid_override
    return config


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _excerpt(text: str, limit: int = 120) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}…"


def _generate_seed(topic: str, tweet: str) -> int:
    """Generate a deterministic seed so humanization is repeatable for a topic."""
    seed_source = f"{topic}:{tweet}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(seed_source).digest()[:4], "big")


def _parse_json_array(text: str) -> list[str]:
    cleaned = _strip_code_fences(text)
    excerpt = _excerpt(cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start == -1 or end == -1:
            raise ValueError(
                f"Failed to parse LLM response as JSON array. Response excerpt: {excerpt!r}"
            ) from exc
        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc_inner:
            raise ValueError(
                f"Failed to parse extracted JSON array from LLM response. Response excerpt: {excerpt!r}"
            ) from exc_inner
    if not isinstance(data, list):
        raise ValueError(
            f"LLM response was not a JSON array (got {type(data).__name__})"
        )
    return [str(item).strip() for item in data if str(item).strip()]


def _trim_tweet(text: str) -> str:
    if len(text) <= TWEET_MAX_LENGTH:
        return text
    max_body = TWEET_MAX_LENGTH - len(ELLIPSIS)
    return text[:max_body].rstrip() + ELLIPSIS


async def _generate_tweets(req: TweetRequest) -> TweetResponse:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "OPENAI_API_KEY environment variable is required but not configured. "
                "Set it in your environment or .env file."
            ),
        )

    config = _build_config(req)
    news_items = await gather_news(
        req.topic,
        use_newsapi=req.use_newsapi,
        news_api_key=settings.news_api_key,
        news_api_hours=settings.news_api_hours,
        news_limit=settings.news_limit,
    )
    news_summary = news_to_bullets(news_items)

    system_prompt = SYSTEM_TEMPLATE.format(
        persona=config["persona"],
        writing_style=config["writing_style"],
        viral_guide=config["viral_guide"],
        avoid=config["avoid"],
        news_summaries=news_summary,
    )
    user_prompt = USER_TEMPLATE.format(topic=req.topic, num_tweets=req.num_tweets)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response_text = await chat_completion(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            messages=messages,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
        )
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    tweets = _parse_json_array(response_text)
    humanized: list[str] = []
    for tweet in tweets:
        seed = _generate_seed(req.topic, tweet)
        humanized.append(_trim_tweet(humanize_tweet(tweet, seed=seed)))
    tweets = humanized

    sources = [item.url for item in news_items if item.url]
    await asyncio.to_thread(
        save_run,
        path=settings.database_path,
        topic=req.topic,
        config=config,
        tweets=tweets,
        sources=sources,
    )

    return TweetResponse(
        topic=req.topic,
        tweets=tweets,
        sources=sources,
        used_news_count=len(news_items),
    )


async def _scheduled_job(topic: str, num_tweets: int) -> None:
    req = TweetRequest(topic=topic, num_tweets=num_tweets)
    await _generate_tweets(req)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "scheduler": settings.scheduler_enabled}


@app.post("/generate", response_model=TweetResponse)
async def generate(req: TweetRequest) -> TweetResponse:
    return await _generate_tweets(req)


@app.post("/schedule", response_model=ScheduleResponse)
async def schedule(req: ScheduleRequest) -> ScheduleResponse:
    if not settings.scheduler_enabled:
        raise HTTPException(
            status_code=400,
            detail=(
                "Scheduling is disabled. Set SCHEDULER_ENABLED to true, yes, 1, or on "
                "to enable."
            ),
        )
    interval = req.interval_minutes or settings.schedule_interval_minutes
    job_id = f"topic-{uuid.uuid4().hex[:10]}"
    scheduler.add_interval_job(
        job_id,
        interval,
        _scheduled_job,
        req.topic,
        req.num_tweets,
    )
    return ScheduleResponse(job_id=job_id, interval_minutes=interval, topic=req.topic)
