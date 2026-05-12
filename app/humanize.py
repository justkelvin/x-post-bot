from __future__ import annotations

import random
import re

EMOJIS = ["🔥", "🚨", "✨", "🤯", "👀", "🧠"]
STARTERS = ["Honestly", "Hot take", "Current mood", "I can't believe", "Just saw this"]


def humanize_tweet(text: str, seed: int | None = None) -> str:
    rng = random.Random(seed)
    cleaned = re.sub(r"\s+", " ", text).strip()

    if cleaned and cleaned[0].isalpha() and rng.random() < 0.15:
        cleaned = cleaned[0].lower() + cleaned[1:]

    if rng.random() < 0.2 and not any(cleaned.startswith(prefix) for prefix in STARTERS):
        prefix = rng.choice(STARTERS)
        candidate = f"{prefix}: {cleaned}"
        if len(candidate) <= 280:
            cleaned = candidate

    if " and " in cleaned and rng.random() < 0.15:
        cleaned = cleaned.replace(" and ", " & ", 1)

    if not any(char in cleaned for char in EMOJIS) and rng.random() < 0.35:
        emoji = rng.choice(EMOJIS)
        candidate = f"{cleaned} {emoji}"
        if len(candidate) <= 280:
            cleaned = candidate

    return cleaned
