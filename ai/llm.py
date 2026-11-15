"""Thin Gemini wrapper (Google AI Studio free-tier key), used by the Ask page.

Reads GEMINI_API_KEY and GEMINI_MODEL from the environment or .env; the
Streamlit page copies st.secrets into the environment on the hosted app.
Nothing touches the network at import time and google-genai is imported
lazily, so the rest of the app runs with no key and no SDK.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_client = None


class LLMUnavailable(RuntimeError):
    """No API key or model set, SDK missing, or the call failed."""


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ROOT / ".env")


def has_key() -> bool:
    _load_env()
    return bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_MODEL"))


def model_name() -> str:
    _load_env()
    model = os.getenv("GEMINI_MODEL")
    if not model:
        raise LLMUnavailable("GEMINI_MODEL is not set (pick a free Flash model in AI Studio)")
    return model


def _get_client():
    global _client
    if _client is not None:
        return _client
    _load_env()
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise LLMUnavailable("GEMINI_API_KEY is not set (copy .env.example to .env)")
    try:
        from google import genai
    except ImportError as exc:
        raise LLMUnavailable("google-genai is not installed: pip install google-genai") from exc
    _client = genai.Client(api_key=key)
    return _client


def _generate(prompt: str, **config):
    client = _get_client()
    model = model_name()
    from google.genai import types  # lazy

    try:
        return client.models.generate_content(
            model=model, contents=prompt, config=types.GenerateContentConfig(**config)
        )
    except Exception as exc:  # network, quota, auth
        raise LLMUnavailable(f"Gemini call failed: {exc}") from exc


def call_llm_json(prompt: str, schema: dict, *, temperature: float = 0.2) -> dict:
    """One prompt -> dict matching `schema` (Gemini OpenAPI-style schema).

    Raises LLMUnavailable on missing key/SDK or API error, ValueError on bad JSON.
    """
    resp = _generate(prompt, response_mime_type="application/json",
                     response_schema=schema, temperature=temperature)
    return json.loads(resp.text)


def call_llm_text(prompt: str, *, temperature: float = 0.2) -> str:
    """Plain-text completion (Ask page)."""
    return _generate(prompt, temperature=temperature).text or ""
