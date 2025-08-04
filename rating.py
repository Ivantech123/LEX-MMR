"""Core rating logic (Elo-style with legal tweaks)."""
from __future__ import annotations

from math import log10, sqrt
from datetime import date, timedelta
from enum import Enum

from sqlalchemy.orm import Session

from db import CaseOutcome, Lawyer, Case, Review, Penalty, RatingHistory





def initial_rating(years_experience: float, avg_review: float | None) -> float:
    """Start at 1000 then add small bonuses."""
    bonus_exp = 10 * log10(1 + years_experience)
    bonus_reviews = 20 * (avg_review - 3) if avg_review else 0
    return 1000 + bonus_exp + bonus_reviews


def expected_score(rating: float, complexity: int) -> float:
    """Expected probability to win given case complexity.

    Complexity 3 is neutral; >3 harder, <3 easier.
    We shift rating by 50*(complexity-3) to simulate tougher opponents.
    """
    r_adj = rating - 50 * (complexity - 3)
    return 1 / (1 + 10 ** (-(r_adj) / 400))


def k_factor(num_cases: int) -> float:
    """K decreases with experience."""
    return 40 / sqrt(num_cases + 1)


def score_from_outcome(outcome: CaseOutcome) -> float:
    return {
        CaseOutcome.FULL_WIN: 1.0,
        CaseOutcome.PARTIAL_WIN: 0.5,
        CaseOutcome.SETTLEMENT: 0.0,  # Нейтральный исход, не 0.5
        CaseOutcome.LOSS: -1.0,  # Поражение теперь -1.0, а не 0.0
    }[outcome]


def update_rating_for_case(session: Session, lawyer: Lawyer, case: Case) -> None:
    """Apply Elo update for a single case."""
    num_cases = len(lawyer.cases)
    K = k_factor(num_cases)
    E = expected_score(lawyer.current_rating, case.complexity)
    S = score_from_outcome(case.outcome)

    new_rating = lawyer.current_rating + K * (S - E)
    lawyer.current_rating = new_rating
    lawyer.last_active = case.date

    session.add(RatingHistory(lawyer_id=lawyer.id, rating=new_rating))


# ---------- Composite scoring helpers ----------
MAX_ELO = 2400.0
MIN_ELO = 800.0

WEIGHTS = {
    "elo": 0.6,
    "reviews": 0.2,
    "experience": 0.1,
    "media": 0.1,  # placeholder until media data collected
}


def _norm(value: float, min_v: float, max_v: float) -> float:
    """Scale to 0-100 with clamping."""
    return max(0.0, min(100.0, 100 * (value - min_v) / (max_v - min_v)))


def score_reviews_100(lawyer: Lawyer) -> float:
    """Bayesian average of review ratings mapped to 0-100."""
    m = 10  # prior strength
    prior = 3.5
    if not lawyer.reviews:
        avg = prior
    else:
        n = len(lawyer.reviews)
        mean = sum(r.score for r in lawyer.reviews) / n
        avg = (mean * n + prior * m) / (n + m)
    return _norm(avg, 1.0, 5.0)


def score_experience_100(lawyer: Lawyer) -> float:
    return _norm(lawyer.years_experience or 0, 0, 30)


def score_media_100(lawyer: Lawyer) -> float:
    # TODO: real metric later
    return 50.0


def composite_rating(lawyer: Lawyer) -> float:
    elo_norm = _norm(lawyer.current_rating, MIN_ELO, MAX_ELO)
    reviews_norm = score_reviews_100(lawyer)
    exp_norm = score_experience_100(lawyer)
    media_norm = score_media_100(lawyer)

    return (
        WEIGHTS["elo"] * elo_norm
        + WEIGHTS["reviews"] * reviews_norm
        + WEIGHTS["experience"] * exp_norm
        + WEIGHTS["media"] * media_norm
    )


def monthly_adjustments(session: Session, today: date | None = None) -> None:
    """Apply periodic review bonus, penalty deductions and inactivity decay."""
    today = today or date.today()
    month_ago = today - timedelta(days=30)
    inactive_threshold = today - timedelta(days=365)

    lawyers = session.query(Lawyer).all()
    for lw in lawyers:
        # bonus for fresh positive reviews
        recent_reviews = [rev for rev in lw.reviews if rev.date and rev.date >= month_ago]
        if recent_reviews:
            avg_recent = sum(r.score for r in recent_reviews) / len(recent_reviews)
            if avg_recent >= 4.5:
                lw.current_rating += 5

        # penalties
        recent_penalties = [p for p in lw.penalties if p.date and p.date >= month_ago]
        if recent_penalties:
            lw.current_rating -= 30 * len(recent_penalties)

        # inactivity decay
        if not lw.last_active or lw.last_active < inactive_threshold:
            lw.current_rating *= 0.95

        # ---- Compose final score ----
        lw.current_rating = composite_rating(lw)

        session.add(RatingHistory(lawyer_id=lw.id, rating=lw.current_rating))


__all__ = [
    "Outcome",
    "initial_rating",
    "update_rating_for_case",
    "monthly_adjustments",
]
