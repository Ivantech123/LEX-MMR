"""Wrapper to call Perplexity via OpenRouter if direct key absent."""
from __future__ import annotations
import os, json, requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
OR_KEY = os.getenv("OPENROUTER_KEY")
if not OR_KEY:
    raise RuntimeError("Set OPENROUTER_KEY in .env or use direct Perplexity key")

API_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {OR_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://yourdomain.com",  # per OpenRouter policy
    "X-Title": "lawyer-rating-agent",
}

DEFAULT_MODEL_ID = "perplexity/sonar-reasoning-pro"  # high-quality reasoning model


PROMPT_SYS = (
    "You are an assistant rating lawyers with open data. "
    "Return JSON only with keys: overall_rating(0-100), reviews_score, media_mentions, years_experience_est, rationale."
)


def lawyer_snapshot_or(fio: str, city: str = "Саранск") -> Dict[str, Any]:
    body = {
        "model": DEFAULT_MODEL_ID,
        "messages": [
            {"role": "system", "content": PROMPT_SYS},
            {"role": "user", "content": f"Lawyer: {fio}\nCity: {city}"},
        ],
        "temperature": 0.2,
    }
    r = requests.post(API_URL, headers=HEADERS, json=body, timeout=90)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    return json.loads(content)
