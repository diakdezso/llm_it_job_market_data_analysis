"""Streamlit dashboard."""

import pandas as pd
import streamlit as st
from sqlalchemy import func, select

from jobmarket.db import SessionLocal
from jobmarket.models import AIMetric, Country, JobPosting, StatisticalEmploymentData

st.set_page_config(page_title="AI and the IT Job Market", layout="wide")
st.title("AI and the European IT Job Market")

with SessionLocal() as session:
    counts = {model.__tablename__: session.scalar(select(func.count()).select_from(model))
              for model in (Country, JobPosting, StatisticalEmploymentData, AIMetric)}

st.subheader("Rows per table")
st.dataframe(pd.Series(counts, name="rows"))
