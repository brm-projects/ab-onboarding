# A/B Testing Platform (Fintech Onboarding)

This project is a minimal experimentation platform designed to simulate how a fintech startup could test different **onboarding flows**.  

The focus is on **progressive onboarding vs. full KYC upfront** — a realistic and high-impact problem in digital banking.  

## Experiment

- **Variant A (Control):** Full KYC at the start (name, address, ID, selfie).  
- **Variant B (Treatment):** Progressive onboarding (email + phone first, full KYC later).  

### Metrics
- **Primary metric:** % of users completing sign-up.  
- **Guardrails:** % of users completing KYC within 7 days, simulated fraud rate.  

---

## Project Goals

1. **Assignment Service (FastAPI)**  
   - Deterministic randomization into A/B groups.  
   - Sticky assignments: each user always sees the same variant.  
   - Event logging (`signup_start`, `signup_complete`, `kyc_complete`).  

2. **Data Pipeline (SQL + dbt)**  
   - Store raw events.  
   - Transform into exposure and conversion metrics.  

3. **Analysis (Python)**  
   - Classical A/B test (two-proportion z-test).  
   - CUPED variance reduction.  
   - Optional Bayesian analysis.  

4. **Dashboard (Streamlit)**  
   - Visualize traffic allocation, conversion rates, guardrail metrics.  
   - Provide a “ship / hold / stop” recommendation.  

---

## Tech Stack

- **FastAPI** for assignment and event logging  
- **Postgres** for data storage  
- **dbt** for transformations  
- **Python (pandas, statsmodels, PyMC)** for analysis  
- **Streamlit** for experiment dashboard  
- **Docker Compose** for local setup  

---

## Repository Structure

ab-onboarding/
├── api/
├── analysis/
├── dashboard/
├── dbt/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── sources.yml
│   │   ├── staging/
│   │   │   ├── stg_events_raw.sql
│   │   │   └── stg_assignments.sql
│   │   └── marts/
│   │       ├── fct_exposures.sql
│   │       ├── fct_conversions.sql
│   │       ├── agg_experiment_day.sql
│   │       └── schema.yml
│   └── macros/
├── sql/
│   └── init.sql
├── tests/
├── docker-compose.yml
├── requirements.txt
├── .gitignore
└── README.md


## Results

After simulating ~3,000 users...

**Conversion rates (with 95% CI):**

![Conversion rates](results_conversion.png)

**Bayesian posterior distribution of lift (B − A):**

![Posterior lift](results_lift.png)

**How to read the charts**

- **Conversion rates (left chart):** Variant B’s bar is clearly higher than Variant A’s, with narrow error bars. This means the improvement we see is real, not just random noise.

- **Lift distribution (right chart):** The entire curve is to the right of zero, meaning B almost certainly converts more users than A. The shaded range shows we expect the true improvement to be around +12% to +19%.

=> Variant B consistently outperforms A, and the compliance guardrail (KYC within 7 days) also improved. In a real fintech setting, this would justify rolling out Variant B to all new users.

## Quickstart

### Prerequisites
- Docker + Docker Compose
- Python 3.11+ (project tested on 3.11/3.13)

```bash
# 1) Clone + env
git clone https://github.com/brm-projects/ab-onboarding
cd ab-onboarding
cp .env.example .env

# 2) Python env + deps
make venv
make deps

# 3) Postgres
make up

# 4) API (new terminal)
make api   # http://127.0.0.1:8000/health

# 5) Generate traffic
make simulate

# 6) Build marts
make dbt && make test

# 7) Analyze (frequentist and Bayesian)
make analyze
make analyze-bayes
