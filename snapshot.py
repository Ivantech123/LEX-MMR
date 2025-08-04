"""Unified interface to get and validate lawyer snapshot from Perplexity (direct) or via OpenRouter."""
from __future__ import annotations

import os, json
from typing import Optional

from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

from pplx_client import get_lawyer_snapshot as _direct_pplx
from openrouter_client import lawyer_snapshot_or as _or_pplx

load_dotenv()


class LawyerSnapshot(BaseModel):
    overall_rating: float  # 0–100
    reviews_score: Optional[float] = None  # 0–5
    media_mentions: Optional[int] = None
    years_experience_est: Optional[float] = None
    rationale: str


def fetch_snapshot(fio: str, city: str = "Саранск") -> LawyerSnapshot:
    """Try direct Perplexity, fallback to OpenRouter."""
    content: str | dict
    try:
        content = _direct_pplx(fio, city)
    except Exception:
        content = _or_pplx(fio, city)

    if isinstance(content, str):
        data = json.loads(content)
    else:
        data = content
    try:
        return LawyerSnapshot.model_validate(data)
    except ValidationError as e:
        raise RuntimeError(f"Snapshot schema invalid: {e}") from e
