"""Very rough stubs for data collection from open sources.
In practice, you will need API keys, proper parsing, rate-limiting, captcha bypass etc.
"""
from datetime import date
from typing import Iterator, Dict, Any

import requests
from bs4 import BeautifulSoup  # noqa: S410

from db import CaseOutcome, get_session, Lawyer, Case, Review, Penalty
from rating import initial_rating


# --------------------- Court cases ---------------------

def _map_outcome(outcome_str: str) -> CaseOutcome | None:
    """Maps raw string from parser to a CaseOutcome enum."""
    val = outcome_str.lower().strip()
    if "удовлетворено полностью" in val:
        return CaseOutcome.FULL_WIN
    if "удовлетворено частично" in val:
        return CaseOutcome.PARTIAL_WIN
    if "мировое" in val or "прекращено" in val:
        return CaseOutcome.SETTLEMENT
    if "отказано" in val:
        return CaseOutcome.LOSS
    return None


def fetch_cases_gas_pravosudie(lawyer_fio: str) -> Iterator[Dict[str, Any]]:
    """Call unofficial GАС 'Правосудие' search endpoint and yield dicts."""
    # NOTE: Example URL; may require POST + pagination + API key.
    url = "https://bsr.sudrf.ru/api/search"  # fictitious example
    params = {"lawyer": lawyer_fio, "limit": 100}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    for item in resp.json().get("results", []):
        yield {
            "date": date.fromisoformat(item["decision_date"]),
            "complexity": int(item["category_complexity"]),
            "outcome": item["result"],  # map to win/lose/settle later
        }


# --------------------- Reviews (Flamp/2GIS/YMaps) ---------------------

def fetch_reviews_2gis(lawyer_fio: str) -> Iterator[Dict[str, Any]]:
    query_url = f"https://catalog.api.2gis.com/3.0/items?q={lawyer_fio}&types=lawyer"
    # token needed -> pass in headers or params
    resp = requests.get(query_url, timeout=20)
    if resp.status_code != 200:
        return
    for place in resp.json().get("result", {}).get("items", []):
        # second call for reviews endpoint omitted for brevity
        yield {
            "date": date.today(),
            "score": 4.8,
        }


# --------------------- Main ETL ---------------------

def upsert_lawyer(session, fio: str, years_exp: float) -> Lawyer:
    lw = session.query(Lawyer).filter_by(full_name=fio).first()
    if not lw:
        lw = Lawyer(full_name=fio, years_experience=years_exp, start_rating=1000)
        session.add(lw)
        session.flush()
    return lw


def ingest():
    session = get_session()

    # EXAMPLE seed list – replace with your CSV / API input OR add via Streamlit UI
    seed_lawyers = [
        ("Иванов П.А.", 7),
        ("Петрова Е.В.", 12),
    ]

    for fio, exp in seed_lawyers:
        lw = upsert_lawyer(session, fio, exp)

        # Reviews
        reviews = list(fetch_reviews_2gis(fio))
        if reviews:
            for rv in reviews:
                session.add(Review(lawyer_id=lw.id, date=rv["date"], score=rv["score"]))
            avg = sum(r["score"] for r in reviews) / len(reviews)
        else:
            avg = None

        # Initial rating if new
        if lw.start_rating == 1000:  # freshly created
            lw.start_rating = initial_rating(exp, avg)
            lw.current_rating = lw.start_rating

        # Cases
        for case_dict in fetch_cases_gas_pravosudie(fio):
            outcome_enum = _map_outcome(case_dict["outcome"])
            if not outcome_enum:
                print(f"Skipping case with unknown outcome: {case_dict['outcome']}")
                continue

            session.add(
                Case(
                    lawyer_id=lw.id,
                    date=case_dict["date"],
                    complexity=case_dict["complexity"],
                    outcome=outcome_enum,
                )
            )

    session.commit()
    session.close()


if __name__ == "__main__":
    ingest()
