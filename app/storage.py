from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def init_db(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tweet_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                created_at TEXT NOT NULL,
                config_json TEXT NOT NULL,
                sources_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES tweet_runs(id)
            )
            """
        )
        conn.commit()


def save_run(
    *,
    path: str,
    topic: str,
    config: dict,
    tweets: list[str],
    sources: list[str],
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(path) as conn:
        cursor = conn.execute(
            "INSERT INTO tweet_runs (topic, created_at, config_json, sources_json) VALUES (?, ?, ?, ?)",
            (topic, created_at, json.dumps(config), json.dumps(sources)),
        )
        run_id = cursor.lastrowid
        if run_id is None:
            raise RuntimeError(
                f"Failed to insert tweet run into {path}. Check database permissions."
            )
        conn.executemany(
            "INSERT INTO tweets (run_id, text) VALUES (?, ?)",
            [(run_id, tweet) for tweet in tweets],
        )
        conn.commit()
    return int(run_id)
