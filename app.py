"""Streamlit front-end to show dynamic Perplexity-based lawyer ratings."""
import json
from pathlib import Path

import streamlit as st

from db import init_db, get_session, Lawyer
from snapshot import fetch_snapshot

init_db()

st.title("Lawyer Rating – AI snapshot")

city = st.text_input("City", value="Саранск")
new_name = st.text_input("Enter lawyer full name (ФИО) and press Add")
if st.button("Add lawyer") and new_name:
    sess = get_session()
    if not sess.query(Lawyer).filter_by(full_name=new_name).first():
        lw = Lawyer(full_name=new_name, years_experience=0)
        sess.add(lw)
        sess.commit()
        st.success("Added, now you can refresh rating!")
    sess.close()

if st.button("Refresh ratings via Perplexity"):
    sess = get_session()
    for lw in sess.query(Lawyer).all():
        with st.status(f"Querying {lw.full_name}", expanded=False):
            try:
                raw = get_lawyer_snapshot(lw.full_name, city)
                data = json.loads(raw)
                lw.current_rating = data.get("overall_rating", lw.current_rating)
                sess.add(lw)
            except Exception as e:
                st.warning(f"Failed for {lw.full_name}: {e}")
    sess.commit()
    sess.close()

sess = get_session()
lawyers = sess.query(Lawyer).order_by(Lawyer.current_rating.desc()).all()

st.subheader("Leaderboard")
for rank, lw in enumerate(lawyers, 1):
    st.write(f"{rank}. {lw.full_name} — {lw.current_rating:.1f}")

sess.close()
