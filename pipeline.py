"""Nightly batch: ingest new data, update ratings."""
from datetime import date

from db import init_db, get_session, Lawyer, Case
from data_collect import ingest
from rating import update_rating_for_case, monthly_adjustments


def main():
    init_db()

    # 1. Collect fresh external data and populate DB
    ingest()

    session = get_session()

    # 2. Incrementally update ratings for all new cases (today only for simplicity)
    today_cases = session.query(Case).filter(Case.date == date.today()).all()
    for case in today_cases:
        lw = session.query(Lawyer).get(case.lawyer_id)
        update_rating_for_case(session, lw, case)

    # 3. Apply periodic bonuses/deductions
    monthly_adjustments(session)

    session.commit()
    session.close()


if __name__ == "__main__":
    main()
