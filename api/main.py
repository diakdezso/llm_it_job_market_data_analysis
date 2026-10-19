"""FastAPI backend. Creates the tables and seeds the countries on startup."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from jobmarket.countries import seed_countries
from jobmarket.db import Base, SessionLocal, engine, get_session
from jobmarket.models import Country


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_countries(session)
    yield


app = FastAPI(title="IT Job Market API", lifespan=lifespan)


class CountryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    iso2: str
    iso3: str
    eurostat_code: str
    name: str
    eu_member: bool
    currency: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/countries", response_model=list[CountryOut])
def countries(session: Session = Depends(get_session)):
    return session.scalars(select(Country).order_by(Country.name)).all()
