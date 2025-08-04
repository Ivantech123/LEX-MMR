"""Simple wrapper around Perplexity API (chat completion).
Requires env var PERPLEXITY_API_KEY.
"""
import os
from typing import List
from dotenv import load_dotenv
import requests

load_dotenv()

PPLX_KEY = os.getenv("PERPLEXITY_API_KEY")
if not PPLX_KEY:
    raise RuntimeError("Set PERPLEXITY_API_KEY in .env")

API_URL = "https://api.perplexity.ai/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {PPLX_KEY}",
    "Content-Type": "application/json",
}


PROMPT_TEMPLATE = (
    "You are an assistant helping to rate a Russian lawyer. "
    "Given the lawyer's full name and city, analyse public web data and output JSON with fields: "
    "reviews_score (0-5), media_mentions (count), years_experience (estimate), notable_cases (text), "
    "overall_rating (0-100) with brief rationale. Return only JSON."
)


def get_lawyer_snapshot(fio: str, city: str = "Саранск") -> dict:
    payload = {
        "model": "llama-3-sonar-large-32k-online",
        "messages": [
            {"role": "system", "content": PROMPT_TEMPLATE},
            {
                "role": "user",
                "content": f"Lawyer: {fio}\nCity: {city}",
            },
        ],
        "temperature": 0.2,
    }
    resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
