# x-post-bot

Generate human-feeling, viral X posts from real-time web sources using a configurable prompt and LLM.

## Features
- Real-time data ingestion from Google News RSS and optional NewsAPI.
- Prompt + persona + viral guide layer for consistent voice.
- Optional humanization post-processing.
- FastAPI endpoint for on-demand generation.
- SQLite persistence for generated runs.
- Optional scheduler for recurring generation.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Run the API:

```bash
uvicorn app.main:app --reload
```

## Environment Variables

- `OPENAI_API_KEY` (required): API key for the OpenAI-compatible chat completions endpoint.
- `OPENAI_MODEL` (optional): Defaults to `gpt-4o-mini`.
- `OPENAI_BASE_URL` (optional): Defaults to `https://api.openai.com/v1`.
- `NEWS_API_KEY` (optional): Enables NewsAPI in addition to Google News RSS.
- `DATABASE_PATH` (optional): SQLite path for generated runs.
- `SCHEDULER_ENABLED` (optional): Set `true` to enable scheduling.
- `SCHEDULE_INTERVAL_MINUTES` (optional): Default interval for scheduled jobs.

## API

### POST /generate

```json
{
  "topic": "AI startups",
  "num_tweets": 3,
  "style_override": "Conversational tech blogger, punchy sentences",
  "persona_override": "Late-20s founder testing every AI tool",
  "viral_guide_override": "1. Start bold...",
  "avoid_override": "marketing fluff"
}
```

### POST /schedule

Requires `SCHEDULER_ENABLED=true`.

```json
{
  "topic": "AI regulation",
  "interval_minutes": 60,
  "num_tweets": 2
}
```

### GET /health

Returns API status and scheduler flag.

## Notes
- The LLM output must return a JSON array of strings for reliable parsing.
- When NewsAPI is unavailable, Google News RSS is still used for live context.
