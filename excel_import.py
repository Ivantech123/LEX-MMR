"""Import lawyers from Excel to DB.
Expected columns (case-insensitive):
    - full_name (str)
    - years_experience (float/int, optional)
    - city (str, optional, defaults to 'Саранск')

Usage:
    python excel_import.py export.xlsx
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

from db import init_db, get_session, Lawyer


def main(path: str):
    f = Path(path)
    if not f.exists():
        print("File not found", file=sys.stderr)
        sys.exit(1)

    init_db()
    df = pd.read_excel(f)
    # normalize columns
    cols = {c.lower(): c for c in df.columns}
    if "full_name" not in cols:
        raise ValueError("Excel must contain 'full_name' column")

    session = get_session()
    added = 0
    for _, row in df.iterrows():
        fio = row[cols["full_name"]].strip()
        years = float(row[cols.get("years_experience", "years_experience")]) if "years_experience" in cols else 0
        city = row[cols.get("city", "city")] if "city" in cols else "Саранск"
        if not session.query(Lawyer).filter_by(full_name=fio).first():
            session.add(Lawyer(full_name=fio, years_experience=years))
            added += 1
    session.commit()
    print(f"Imported {added} lawyers")
    session.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python excel_import.py <file.xlsx>")
        sys.exit(1)
    main(sys.argv[1])
