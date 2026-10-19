"""
Data model: one table per kind of data, plus countries for the foreign keys.

    Country                      all European countries (seeded from countries.py)
    JobPosting                   one row per job ad (Adzuna, EURES, LinkedIn, ...)
    StatisticalEmploymentData    one row per published number (Eurostat, ONS, ...)
    AIMetric                     one row per AI indicator (Epoch AI, Hugging Face, ...)

Every table keeps the full source record in `raw`, so no field is lost and
columns can be added later by parsing `raw` again.
"""

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from jobmarket.db import Base

# JSONB on PostgreSQL, plain JSON elsewhere (e.g. SQLite in tests)
RawJSON = JSON().with_variant(JSONB(), "postgresql")


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    iso2: Mapped[str] = mapped_column(String(2), unique=True)           # AT, GB, GR
    iso3: Mapped[str] = mapped_column(String(3), unique=True)           # AUT, GBR, GRC
    eurostat_code: Mapped[str] = mapped_column(String(2), unique=True)  # differs for GR (EL), GB (UK)
    name: Mapped[str] = mapped_column(String(64))
    eu_member: Mapped[bool]
    currency: Mapped[str] = mapped_column(String(3))                    # ISO 4217

    job_postings: Mapped[list["JobPosting"]] = relationship(back_populates="country")
    statistics: Mapped[list["StatisticalEmploymentData"]] = relationship(back_populates="country")
    ai_metrics: Mapped[list["AIMetric"]] = relationship(back_populates="country")


class JobPosting(Base):
    """A job ad. The same ad seen in several snapshots stays one row (first/last_seen_at)."""
    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32))                     # adzuna, eures, linkedin
    external_id: Mapped[str] = mapped_column(String(64))                # the source's ad id
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"))

    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)               # Adzuna: first 500 chars only
    company: Mapped[str | None] = mapped_column(String(256))
    category: Mapped[str | None] = mapped_column(String(64))            # e.g. it-jobs
    location: Mapped[str | None] = mapped_column(String(256))           # as displayed by the source
    location_area: Mapped[str | None] = mapped_column(Text)             # "Österreich > Wien > ..."
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]

    contract_time: Mapped[str | None] = mapped_column(String(32))       # full_time, part_time
    contract_type: Mapped[str | None] = mapped_column(String(32))       # permanent, contract
    remote_type: Mapped[str | None] = mapped_column(String(32))         # onsite, hybrid, remote

    salary_min: Mapped[float | None]
    salary_max: Mapped[float | None]
    salary_currency: Mapped[str | None] = mapped_column(String(3))
    salary_period: Mapped[str | None] = mapped_column(String(16))       # year, month, hour
    salary_is_predicted: Mapped[bool | None]

    url: Mapped[str | None] = mapped_column(Text)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw: Mapped[dict | None] = mapped_column(RawJSON)

    country: Mapped[Country | None] = relationship(back_populates="job_postings")


class StatisticalEmploymentData(Base):
    """
    Official or aggregated labour-market numbers in long format: one value per
    source, country, period, metric and category. Examples:
        eurostat / isoc_sks_itspt / ict_share_pct / -              / 2024 -> 4.8 %
        eurostat / jvs_q_nace2    / vacancy_rate  / NACE J         / 2024-Q1 -> 3.1 %
        adzuna   / history        / mean_salary   / it-jobs        / 2026-09 -> 66,000 EUR
        layoffs  / workforcesignal/ affected_headcount / <company> / 2026-03-12 -> 1,200
    """
    __tablename__ = "statistical_employment_data"
    __table_args__ = (UniqueConstraint("source", "dataset", "country_id", "period",
                                       "frequency", "metric", "category"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32))                     # eurostat, ons, bls, adzuna
    dataset: Mapped[str] = mapped_column(String(64))                    # source's dataset code
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"))
    period: Mapped[date] = mapped_column(Date)                          # first day of the period
    frequency: Mapped[str] = mapped_column(String(1))                   # A, Q, M, D
    metric: Mapped[str] = mapped_column(String(64))                     # ict_ths, vacancy_rate, ...
    category: Mapped[str] = mapped_column(String(128), default="")      # ISCO/NACE code, role, company
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))                # %, THS, EUR
    notes: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw: Mapped[dict | None] = mapped_column(RawJSON)

    country: Mapped[Country | None] = relationship(back_populates="statistics")


class AIMetric(Base):
    """
    AI progress and adoption indicators, one value per subject, date and metric.
    Examples:
        epoch_ai      / notable_models / GPT-5 (OpenAI)     / training_compute_flop
        huggingface   / open_llm_lb    / Llama-3-70B        / mmlu_score
        stackoverflow / survey_2025    / developers (AT)    / uses_ai_tools_pct
        github        / octoverse      / repositories (DE)  / genai_projects
    `metric`/`value` may stay empty when only the raw record is stored.
    """
    __tablename__ = "ai_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32))                     # epoch_ai, huggingface, ...
    dataset: Mapped[str] = mapped_column(String(64))
    subject: Mapped[str | None] = mapped_column(String(256))            # model, benchmark, population
    organization: Mapped[str | None] = mapped_column(String(256))       # model developer
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"))
    reference_date: Mapped[date | None] = mapped_column(Date)           # release / survey / eval date
    metric: Mapped[str | None] = mapped_column(String(64))
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw: Mapped[dict | None] = mapped_column(RawJSON)

    country: Mapped[Country | None] = relationship(back_populates="ai_metrics")
