from __future__ import annotations

from dataclasses import dataclass

import httpx

XQUIK_TWEETS_PATH = "/api/v1/x/tweets"


class XquikPublishError(RuntimeError):
    """Raised when Xquik does not accept or confirm a tweet publish request."""


@dataclass(frozen=True)
class XquikTweetResult:
    text: str
    tweet_id: str
    url: str


def _tweet_url(tweet_id: str) -> str:
    return f"https://x.com/i/status/{tweet_id}"


def _read_error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"Xquik request failed with HTTP {response.status_code}"

    if isinstance(body, dict):
        message = body.get("message") or body.get("error")
        if isinstance(message, str) and message.strip():
            return message.strip()

    return f"Xquik request failed with HTTP {response.status_code}"


async def _publish_text(
    client: httpx.AsyncClient,
    text: str,
    *,
    account: str,
    api_key: str,
    base_url: str,
) -> XquikTweetResult:
    endpoint = f"{base_url.rstrip('/')}{XQUIK_TWEETS_PATH}"
    try:
        response = await client.post(
            endpoint,
            headers={"x-api-key": api_key},
            json={"account": account, "text": text},
        )
    except httpx.HTTPError as exc:
        raise XquikPublishError(f"Xquik request failed: {exc}") from exc

    if response.status_code >= 400:
        raise XquikPublishError(_read_error_message(response))

    try:
        body = response.json()
    except ValueError as exc:
        raise XquikPublishError("Xquik response was not valid JSON.") from exc

    if not isinstance(body, dict):
        raise XquikPublishError("Xquik response was not a JSON object.")

    tweet_id = body.get("tweetId")
    if not isinstance(tweet_id, str) or not tweet_id.strip():
        raise XquikPublishError("Xquik response did not include a tweet ID.")

    return XquikTweetResult(
        text=text,
        tweet_id=tweet_id.strip(),
        url=_tweet_url(tweet_id.strip()),
    )


async def publish_texts(
    texts: list[str],
    *,
    account: str,
    api_key: str,
    base_url: str,
    client: httpx.AsyncClient | None = None,
) -> list[XquikTweetResult]:
    if not api_key.strip() or not account.strip():
        raise XquikPublishError("XQUIK_API_KEY and XQUIK_ACCOUNT are required.")

    if client is not None:
        results = []
        for text in texts:
            results.append(
                await _publish_text(
                    client,
                    text,
                    account=account,
                    api_key=api_key,
                    base_url=base_url,
                )
            )
        return results

    async with httpx.AsyncClient(timeout=20.0) as client:
        results = []
        for text in texts:
            results.append(
                await _publish_text(
                    client,
                    text,
                    account=account,
                    api_key=api_key,
                    base_url=base_url,
                )
            )
        return results
