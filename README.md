# llm_it_job_market_data_analysis

**AI and the European IT Job Market**: a data science project measuring how AI changes demand, skills and salaries in IT jobs.

## Short description

We measure how the rise of AI is changing the IT job market, with a focus on Europe. A data pipeline combines job ads (Adzuna, EURES and others), official labour-market statistics (Eurostat and national statistics offices) and AI indicators (Epoch AI, Hugging Face, Stack Overflow, GitHub) in one PostgreSQL database. A Streamlit dashboard shows how demand, required skills and salaries develop over time and across countries, and how they correlate with AI progress and adoption.

## Long description

### Motivation

Statisticians, data scientists, data engineers, software engineers, job seekers and company leaders all ask the same question: what is AI actually doing to tech jobs? Public answers are often driven by hype. This project replaces opinions with evidence from job ads, official statistics and AI indicators, so that each group can make better career, learning and hiring decisions.

### Research questions

Derived from our six user stories:

1. **Demand:** How does demand for data science, AI, data engineering and software roles change over time and across countries? Is IT employment still growing while hiring slows down?
2. **Skills:** Is demand for AI-related skills (ML, LLMs, GenAI, MLOps, agents) growing faster than for traditional skills (SQL, Java, ETL, BI, cloud)? Which tools are really requested and which are only hype?
3. **Tasks:** Which tasks appear less often in ads, and which new AI-support tasks are redefining roles such as data engineer or data analyst?
4. **Salary:** Which roles, skills, seniority levels and countries pay the most, and do AI skills carry a salary premium?
5. **AI effect:** Do changes in job ads and employment correlate with AI progress (model releases, benchmark scores), AI adoption among developers and AI-related layoffs?
6. **Employers:** Which companies hire for which skills, and what are competitors looking for?

### Method

1. **Collection:** scripts in `scripts/data/` download each source into `data/<source>/` as CSV. Job ads are collected as regular snapshots, because the APIs only return live ads.
2. **Pipeline:** cleaning (duplicates, placeholder salaries, employer names), loading into PostgreSQL, deriving roles, seniority and skill mentions (keyword dictionary in English and German) from the ad texts.
3. **Analysis:** skill shares per month, country and role; growth of AI vs. traditional skills; correlations between job-ad trends, official employment and vacancy numbers, salaries and AI indicators.
4. **Dashboard:** Streamlit app with filters for country, role and time range: demand trends, skill rankings, AI vs. traditional skills, salaries, employers and AI indicators.

### Limitations

- Adzuna descriptions are cut after 500 characters, so skill shares are underestimates.
- Job APIs only return live ads, so ad trends start with our first snapshot; the Adzuna salary history covers 12 months.
- Eurostat data is annual or quarterly counts without skills or salaries; some countries have gaps.
- Most ads have no salary, and advertised salaries differ from real pay.
- A keyword mention is not always a job requirement, and correlation is not causation.

## Data sources

| Source | What we use | Table |
|---|---|---|
| [Adzuna](https://developer.adzuna.com/) | live IT ads for AT, BE, CH, DE, ES, FR, GB, IT, NL, PL; monthly mean IT salary (see `docs/adzuna_coverage_report_it.pdf`) | `job_postings`, `statistical_employment_data` |
| [EURES](https://eures.europa.eu/) | job postings across ~30 European countries | `job_postings` |
| [LinkedIn Job Postings 2023-24 (Kaggle)](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) | historical ads with salaries (US only, filter by `industry_name`) | `job_postings` |
| [Techmap](https://jobdatafeeds.com/job-api), [JobsPipe](https://jobspipe.dev/jobs-api), [CleanJobData](https://cleanjobdata.com/) | job postings (free tiers) | `job_postings` |
| [Eurostat](https://ec.europa.eu/eurostat/web/main/data/database) | ICT specialists in employment, employment by ISCO occupation (25, 35), job vacancy rate NACE J vs. total, 2019-2025 | `statistical_employment_data` |
| [ONS](https://www.ons.gov.uk/), [Destatis](https://www.destatis.de/), [INSEE](https://www.insee.fr/) | national employment and wage statistics | `statistical_employment_data` |
| [BLS](https://www.bls.gov/developers/), [Census / ACS](https://data.census.gov/) | US employment, occupation wages (comparison) | `statistical_employment_data` |
| [e-Stat](https://www.e-stat.go.jp/en), [data.gov.sg](https://data.gov.sg/), [KOSIS](https://kosis.kr/eng/), [data.gov.in](https://data.gov.in/) | Asian labour-force data (comparison) | `statistical_employment_data` |
| [World Bank](https://data.worldbank.org/), [ILOSTAT](https://ilostat.ilo.org/data/) | macro and labour-force indicators | `statistical_employment_data` |
| [Levels.fyi](https://www.levels.fyi/), [Second Talent](https://www.secondtalent.com/asia-tech-salary-index/) | tech compensation benchmarks | `statistical_employment_data` |
| [WorkforceSignal](https://workforcesignal.com/layoff-tracker), [Crunchbase](https://news.crunchbase.com/startups/tech-layoffs/), [AILayoffs.live](https://ailayoffs.live/), [layoffhedge](https://layoffhedge.com/data/) | tech and AI-related layoffs | `statistical_employment_data` |
| [Epoch AI](https://epoch.ai/data/ai-models) | 3,600+ notable AI models (release date, compute, parameters, organization) | `ai_metrics` |
| [Hugging Face datasets](https://huggingface.co/datasets) | LLM benchmark results | `ai_metrics` |
| [Stack Overflow Survey](https://survey.stackoverflow.co/) | developer AI use, roles, salaries by country | `ai_metrics`, `statistical_employment_data` |
| [GitHub Octoverse](https://github.blog/news-insights/octoverse/) | developer and AI ecosystem indicators | `ai_metrics` |

## Data model

Defined in `jobmarket/models.py`. Each table stores the complete source record in `raw` (JSONB), so all fields are kept and can be filtered later.

| Table | One row per | Main columns |
|---|---|---|
| `countries` | European country (47, seeded on API start) | `iso2`, `iso3`, `eurostat_code` (EL, UK), `name`, `eu_member`, `currency` |
| `job_postings` | job ad, unique per `source` + `external_id` | title, description, company, category, location, coordinates, contract, salary min/max/currency/period, `posted_at`, `first_seen_at` / `last_seen_at` |
| `statistical_employment_data` | published number (long format) | `source`, `dataset`, `country_id`, `period`, `frequency` (A/Q/M/D), `metric`, `category` (ISCO/NACE code, role, company), `value`, `unit` |
| `ai_metrics` | AI indicator | `source`, `dataset`, `subject` (model, benchmark, population), `organization`, `country_id`, `reference_date`, `metric`, `value`, `unit` |

`country_id` is a foreign key to `countries` and may be empty (non-European or global data).

## Tech stack

PostgreSQL, SQLAlchemy 2, FastAPI + Pydantic, Streamlit, pandas, all run with Docker Compose.

## Project structure

```
api/main.py            FastAPI app (creates tables, seeds countries)
dashboard/app.py       Streamlit dashboard
jobmarket/             shared code: db.py, models.py, countries.py
scripts/data/          data collection scripts
  adzuna.py            all Adzuna endpoints for one country and keyword
  coverage.py          Adzuna coverage per country
  it_europe.py         all European IT ads + monthly mean IT salary (resumable)
data/<source>/         downloaded CSV / JSON files
notebooks/             exploration notebooks
docs/                  reports
```

## Getting started

```bash
cp .env.example .env          # add the Adzuna keys
docker compose up --build
```

- API: http://localhost:8000/docs
- Dashboard: http://localhost:8501

Collect data (on the host, `pip install -r requirements.txt` first):

```bash
python scripts/data/it_europe.py          # resumes; ~2,600 calls in total, run daily until complete
python scripts/data/it_europe.py --new    # start a new snapshot
```
