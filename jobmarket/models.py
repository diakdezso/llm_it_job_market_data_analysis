"""
Data model: one table per kind of data, plus countries for the foreign keys.
Scope: 10 European countries covered by Adzuna — AT, BE, CH, DE, ES, FR, GB, IT, NL, PL.

    Country              the 10 Adzuna countries (seeded on API start)
    JobPosting           one row per job ad (Adzuna, EURES)
    EurostatICTStats     annual ICT labour-market stats per country (Eurostat)
    AdzunaSalaryHistory  monthly mean advertised IT salary per country (Adzuna)
    AIModel              one row per notable AI model (Epoch AI notable_models)
    AIBenchmark          one benchmark score per model (Epoch AI capability index)

Every table keeps the full source record in `raw`, so no field is lost and
columns can be added later by parsing `raw` again.
"""

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from jobmarket.db import Base

# JSONB on PostgreSQL, plain JSON elsewhere (e.g. SQLite in tests)
RawJSON = JSON().with_variant(JSONB(), "postgresql")


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    iso2: Mapped[str] = mapped_column(String(2), unique=True)           # AT, GB — used by Adzuna API
    eurostat_code: Mapped[str] = mapped_column(String(2), unique=True)  # Eurostat geo code (EL, UK differ)
    name: Mapped[str] = mapped_column(String(64))
    eu_member: Mapped[bool]
    currency: Mapped[str] = mapped_column(String(3))                    # ISO 4217; needed for salary_*_eur

    job_postings: Mapped[list["JobPosting"]] = relationship(back_populates="country")
    eurostat_stats: Mapped[list["EurostatICTStats"]] = relationship(back_populates="country")
    salary_history: Mapped[list["AdzunaSalaryHistory"]] = relationship(back_populates="country")
    ai_models: Mapped[list["AIModel"]] = relationship(back_populates="country")


class JobPosting(Base):
    """A job ad. The same ad seen in several snapshots stays one row (first/last_seen_at)."""
    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32))                     # adzuna, eures
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
    salary_min_eur: Mapped[float | None]                                # pipeline-derived EUR equivalent
    salary_max_eur: Mapped[float | None]

    url: Mapped[str | None] = mapped_column(Text)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw: Mapped[dict | None] = mapped_column(RawJSON)

    country: Mapped[Country | None] = relationship(back_populates="job_postings")


class EurostatICTStats(Base):
    """
    Annual Eurostat ICT labour-market statistics, one row per (country, year).
    Pre-filtered to: working-age (15-64), total sex, NSA, enterprises GE10.
    Sources: ISOC_SKS_ITSPT, LFSA_EGAI2D, JVS_Q_NACE2.
    """
    __tablename__ = "eurostat_ict_stats"
    __table_args__ = (UniqueConstraint("country_id", "year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    year: Mapped[int] = mapped_column(Integer)

    # ISOC_SKS_ITSPT — ICT specialists in employment
    ict_share_pct: Mapped[float | None] = mapped_column(Float)          # % of total employment
    ict_ths: Mapped[float | None] = mapped_column(Float)                # thousands of persons

    # LFSA_EGAI2D — employment by ISCO-08 occupation group, thousands of persons
    oc25_ths: Mapped[float | None] = mapped_column(Float)               # ISCO-08 group 25: ICT professionals
    oc35_ths: Mapped[float | None] = mapped_column(Float)               # ISCO-08 group 35: ICT technicians

    # JVS_Q_NACE2 — job vacancy rates, annual average of quarterly values
    vac_j: Mapped[float | None] = mapped_column(Float)                  # vacancy rate, NACE J (%)
    vac_j_nq: Mapped[int | None] = mapped_column(Integer)               # quarters averaged for vac_j
    vac_total: Mapped[float | None] = mapped_column(Float)              # vacancy rate, total economy (%)
    vac_total_nq: Mapped[int | None] = mapped_column(Integer)           # quarters averaged for vac_total

    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw: Mapped[dict | None] = mapped_column(RawJSON)

    country: Mapped[Country] = relationship(back_populates="eurostat_stats")


class AdzunaSalaryHistory(Base):
    """
    Monthly mean advertised IT salary from Adzuna, one row per (country, month).
    Source: /jobs/{country}/history?category=it-jobs&months=240.
    On re-collection the existing row is kept (historical salary data is stable).
    """
    __tablename__ = "adzuna_salary_history"
    __table_args__ = (UniqueConstraint("country_id", "month"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    month: Mapped[date] = mapped_column(Date)                           # first day of the month
    mean_salary: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(3))             # ISO 4217 (GBP, CHF, EUR, ...)
    mean_salary_eur: Mapped[float | None] = mapped_column(Float)        # pipeline-derived
    snapshot_date: Mapped[date | None] = mapped_column(Date)            # collection date
    raw: Mapped[dict | None] = mapped_column(RawJSON)

    country: Mapped[Country] = relationship(back_populates="salary_history")


class AIModel(Base):
    """
    One row per notable AI model (Epoch AI notable_models dataset). Key numeric metrics
    as columns so cross-metric queries work without self-joins.
    """
    __tablename__ = "ai_models"
    __table_args__ = (UniqueConstraint("name", "organization"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))                      # display name, e.g. "Baichuan 2-7B"
    organization: Mapped[str | None] = mapped_column(String(256))
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"))
    reference_date: Mapped[date | None] = mapped_column(Date)           # publication date
    domain: Mapped[str | None] = mapped_column(String(128))             # Language, Vision, Multimodal, ...
    is_foundation: Mapped[bool | None]
    is_frontier: Mapped[bool | None]
    open_weights: Mapped[bool | None]
    parameters: Mapped[float | None] = mapped_column(Float)
    training_compute_flop: Mapped[float | None] = mapped_column(Float)
    training_dataset_size: Mapped[float | None] = mapped_column(Float)  # total tokens / bytes
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw: Mapped[dict | None] = mapped_column(RawJSON)

    country: Mapped[Country | None] = relationship(back_populates="ai_models")
    benchmarks: Mapped[list["AIBenchmark"]] = relationship(back_populates="ai_model")


class AIBenchmark(Base):
    """
    One benchmark score per (model, benchmark) pair. Source: Epoch AI capability index.
    Enables time-series queries like "how did MMLU scores evolve across model release dates?"
    which are required for correlating AI capability jumps with job market shifts.
    """
    __tablename__ = "ai_benchmarks"
    __table_args__ = (UniqueConstraint("ai_model_id", "benchmark"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ai_model_id: Mapped[int] = mapped_column(ForeignKey("ai_models.id"))
    model_version: Mapped[str | None] = mapped_column(String(256))      # technical id, e.g. HuggingFace slug
    benchmark: Mapped[str] = mapped_column(String(128))                 # ARC, MMLU, GSM8K, GPQA, ...
    benchmark_release_date: Mapped[date | None] = mapped_column(Date)
    performance: Mapped[float | None] = mapped_column(Float)            # normalised 0-1 score
    source_citation: Mapped[str | None] = mapped_column(Text)           # paper title or URL
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw: Mapped[dict | None] = mapped_column(RawJSON)

    ai_model: Mapped[AIModel] = relationship(back_populates="benchmarks")
