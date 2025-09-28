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
├─ api/ # FastAPI service
│ ├─ main.py
│ ├─ config.py
│ └─ experiments.yaml
├─ sql/ # database schema and seeds
│ └─ init.sql
├─ dashboard/ # Streamlit app
│ └─ app.py
├─ analysis/ # Jupyter notebooks for analysis
│ └─ 01_exploration.ipynb
├─ tests/ # pytest unit tests
│ └─ test_assignment.py
├─ requirements.txt # Python dependencies
├─ docker-compose.yml # containers for Postgres etc.
├─ .gitignore
└─ README.md
