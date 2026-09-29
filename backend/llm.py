"""OpenAI-compatible client. Out-of-process by design: llama.cpp here, GenieX on Snapdragon."""
import json, httpx
from . import config


class LLMDown(Exception):
    pass


def chat(messages, temperature=0.2, max_tokens=800, json_mode=False):
    body = {"model": config.LLM_MODEL, "messages": messages,
            "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        r = httpx.post(f"{config.LLM_BASE_URL}/chat/completions", json=body, timeout=180)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise LLMDown(
            "Local model not running. Start it with:\n"
            "  powershell -File scripts\start_llm.ps1\n"
            f"({e})")
    return r.json()["choices"][0]["message"]["content"]


def chat_json(messages, **kw):
    """Small models produce JSON wrapped in prose or fences. Salvage it rather than regenerating."""
    raw = chat(messages, json_mode=True, **kw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    s = raw.find("{") if raw.find("{") >= 0 else raw.find("[")
    e = max(raw.rfind("}"), raw.rfind("]"))
    if s >= 0 and e > s:
        try:
            return json.loads(raw[s:e + 1])
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Model did not return parseable JSON: {raw[:200]}")


def healthy():
    try:
        httpx.get(f"{config.LLM_BASE_URL}/models", timeout=3).raise_for_status()
        return True
    except httpx.HTTPError:
        return False


def chat_stream(messages, temperature=0.2, max_tokens=800):
    """Yield content deltas as they arrive.

    Streaming is not cosmetic here: on this hardware a full answer takes ~13 s, and a student
    staring at a blank panel for 13 s assumes it has hung. First token arrives in about one.
    """
    body = {"model": config.LLM_MODEL, "messages": messages, "temperature": temperature,
            "max_tokens": max_tokens, "stream": True}
    try:
        with httpx.stream("POST", f"{config.LLM_BASE_URL}/chat/completions",
                          json=body, timeout=180) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload.strip() == "[DONE]":
                    return
                try:
                    delta = json.loads(payload)["choices"][0].get("delta", {})
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                if delta.get("content"):
                    yield delta["content"]
    except httpx.HTTPError as e:
        raise LLMDown(f"Local model not running or dropped the connection. ({e})")
