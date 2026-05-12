from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_VIRAL_GUIDE = (
    "1. Start with a bold statement or surprising statistic.\n"
    "2. Use a question hook in the first line.\n"
    "3. Include 1-2 emojis (max).\n"
    "4. End with a call-to-action (retweet if…).\n"
    "5. Keep it under 240 characters when possible.\n"
    "6. Add a trending but relevant hashtag.\n"
    "7. Make it feel urgent / breaking."
)

DEFAULT_CONFIG = {
    "topic": "AI & LLMs",
    "writing_style": (
        "Conversational tech blogger, uses short punchy sentences, "
        "occasional sarcasm, first-person anecdotes"
    ),
    "viral_guide": DEFAULT_VIRAL_GUIDE,
    "persona": "A late-20s startup founder who tests every AI tool",
    "avoid": "marketing fluff, generic phrases like 'game-changer'",
}


def _get_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.9"))
    openai_max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "500"))

    news_api_key: str | None = os.getenv("NEWS_API_KEY")
    news_api_hours: int = int(os.getenv("NEWS_API_HOURS", "2"))
    news_limit: int = int(os.getenv("NEWS_LIMIT", "5"))

    database_path: str = os.getenv("DATABASE_PATH", "./x_post_bot.sqlite")

    scheduler_enabled: bool = _get_bool(os.getenv("SCHEDULER_ENABLED"), False)
    schedule_interval_minutes: int = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "30"))


settings = Settings()
