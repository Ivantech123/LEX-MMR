"""Utilities to import lawyers from CSV/Excel tables."""
from __future__ import annotations
import pandas as pd
from typing import Literal

from db import get_session, Lawyer
from rating import initial_rating


def import_lawyer_table(path: str, city: str | None = None) -> None:
    """Read table (csv/xlsx) with columns: fio, years_exp, [current_rating]."""
    if path.lower().endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    required = {"fio", "years_exp"}
    if not required.issubset(df.columns.str.lower()):
        raise ValueError(f"Table must contain columns: {required}")

    sess = get_session()
    for _, row in df.iterrows():
        fio = row["fio"]
        years = float(row["years_exp"])
        lw = sess.query(Lawyer).filter_by(full_name=fio).first()
        if not lw:
            lw = Lawyer(full_name=fio, years_experience=years)
            # set initial rating baseline (will be replaced after Perplexity fetch)
            lw.start_rating = initial_rating(years, None)
            lw.current_rating = lw.start_rating
            sess.add(lw)
    sess.commit()
    sess.close()

    print(f"Imported {len(df)} lawyers from {path}")
