from __future__ import annotations

import httpx


class LLMError(RuntimeError):
    pass


def _extract_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
        message = payload.get("error", {}).get("message") or payload.get("message")
        if message:
            return str(message)
    except ValueError:
        pass
    return response.text[:500]


async def chat_completion(
    *,
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> str:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
        if response.status_code >= 400:
            error_detail = _extract_error(response)
            raise LLMError(f"LLM request failed: {response.status_code} {error_detail}")
        data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise LLMError(
            f"LLM response contained no choices. Response keys: {list(data.keys())}"
        )
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise LLMError(
            f"LLM response contained no content. Message keys: {list(message.keys())}"
        )
    return content
