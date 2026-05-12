from __future__ import annotations

import httpx


class LLMError(RuntimeError):
    pass


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
            raise LLMError(f"LLM request failed: {response.status_code} {response.text}")
        data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise LLMError("LLM response contained no choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise LLMError("LLM response contained no content")
    return content
