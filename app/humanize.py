from __future__ import annotations

import random
import re

from app.models import TWEET_MAX_LENGTH

EMOJIS = ["🔥", "🚨", "✨", "🤯", "👀", "🧠"]
STARTERS = ["Honestly", "Hot take", "Current mood", "I can't believe", "Just saw this"]
LOWERCASE_PROBABILITY = 0.15
STARTER_PROBABILITY = 0.2
AMPERSAND_PROBABILITY = 0.15
EMOJI_PROBABILITY = 0.35


def humanize_tweet(text: str, seed: int | None = None) -> str:
    rng = random.Random(seed)
    cleaned = re.sub(r"\s+", " ", text).strip()

    if cleaned and cleaned[0].isalpha() and rng.random() < LOWERCASE_PROBABILITY:
        cleaned = cleaned[0].lower() + cleaned[1:]

    if rng.random() < STARTER_PROBABILITY and not any(cleaned.startswith(prefix) for prefix in STARTERS):
        prefix = rng.choice(STARTERS)
        candidate = f"{prefix}: {cleaned}"
        if len(candidate) <= TWEET_MAX_LENGTH:
            cleaned = candidate

    if " and " in cleaned and rng.random() < AMPERSAND_PROBABILITY:
        cleaned = cleaned.replace(" and ", " & ", 1)

    if not any(char in cleaned for char in EMOJIS) and rng.random() < EMOJI_PROBABILITY:
        emoji = rng.choice(EMOJIS)
        candidate = f"{cleaned} {emoji}"
        if len(candidate) <= TWEET_MAX_LENGTH:
            cleaned = candidate

    return cleaned
