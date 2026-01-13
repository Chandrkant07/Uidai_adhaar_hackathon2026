# AadhaarGyan – Project Report (UIDAI Hackathon 2026)

**Project / Website Name:** AadhaarGyan  
**Codebase / Python package:** `aadhaarpulse` (kept as-is to avoid breaking imports)  
**Date:** 2026-01-14  
**Repository:** https://github.com/Chandrkant07/Uidai_adhaar_hackathon2026  

---

## 1) Executive summary
AadhaarGyan is a district-level decision intelligence system built on **aggregated** UIDAI enrolment and update datasets. It converts routine Aadhaar activity (enrolments, demographic updates, biometric updates) into an **early-warning service demand map** that helps UIDAI:

- **Predict** near-term enrolment/update workloads (6–12 months).
- **Detect** unusual spikes/drops (anomaly watchlist).
- **Rank** operational stress at district-month level using **ASSI (Aadhaar Service Stress Index)**.
- **Recommend** targeted interventions (Intervention Planner).
- **Simulate** policy levers (what-if: add centres / biometric drives) and estimate stress reduction.

The system is packaged as:
- A reproducible **pipeline** (CLI) that turns raw CSV dumps into curated parquet + tables.
- A **Streamlit dashboard** for elastic exploration and operational decisioning.

---

## 2) Problem statement (governance framing)
UIDAI operates one of the world’s largest identity infrastructures. Even without using individual-level data, **aggregated** enrolment and update volumes contain strong operational signals:

- **Enrolments** indicate onboarding demand and inclusion momentum.
- **Demographic updates** (address/mobile/etc.) indicate mobility, life events, and friction.
- **Biometric updates** indicate age transitions, ageing refresh needs, and credential quality maintenance.

At UIDAI scale, small percentage shifts translate into large workload swings. AadhaarGyan treats Aadhaar activity as a **public-service demand signal** (similar to power-grid load), producing a continuous “identity load map” of India.

---

## 3) Datasets used (official UIDAI – aggregated)
AadhaarGyan uses aggregated datasets organised under a `--data-root` folder:

- `api_data_aadhar_enrolment/` – aggregated enrolment records
- `api_data_aadhar_demographic/` – aggregated demographic update records
- `api_data_aadhar_biometric/` – aggregated biometric update records

### Data health snapshot (from generated `reports/tables/data_health.csv`)
When the pipeline was last run, the project produced the following scale indicators:

- Enrolment raw rows: **1,006,029**
- Demographic raw rows: **2,071,700**
- Biometric raw rows: **1,861,108**
- District-month panel rows: **8,699**
- Districts: **1,131**
- States: **68**
- Months: **9**

> Note: These numbers reflect the current dataset slices committed in this workspace and will vary with different extraction windows.

---

## 4) System architecture (pipeline → intelligence → actions)
AadhaarGyan is designed as a layered, auditable system.

### High-level flow
```mermaid
flowchart LR
  A[Raw UIDAI Aggregated CSVs\n(api_data_*)] --> B[Cleaning & Harmonisation\n(district, month)]
  B --> C[District-Month Panel\n(parquet)]
  C --> D[Signals & Features\n(migration, ageing, inclusion, etc.)]
  D --> E[ASSI\n(Stress Index 0-100)]
  D --> F[Anomaly Detection\n(spikes / drops)]
  D --> G[Forecasting\n(12-month horizon)]
  E --> H[Rankings\nTop districts]
  F --> I[Watchlists]
  G --> J[Future workload tables]
  H --> K[What-if Simulator\n(centres / drives)]
  I --> L[Streamlit Dashboard]
  J --> L
  K --> L
```

### Implementation map (actual modules)
- Ingestion: `src/aadhaarpulse/pipelines/io.py`
- Cleaning: `src/aadhaarpulse/pipelines/cleaning.py`
- Panel build: `src/aadhaarpulse/pipelines/panel.py`
- Signals: `src/aadhaarpulse/features/signals.py`
- Anomalies & growth: `src/aadhaarpulse/pipelines/analysis.py`
- ASSI: `src/aadhaarpulse/features/assi.py`
- Forecasting: `src/aadhaarpulse/models/forecasting.py`
- What-if simulation: `src/aadhaarpulse/simulator/what_if.py`
- End-to-end runner: `src/aadhaarpulse/pipelines/run_all.py`
- CLI entry: `src/aadhaarpulse/cli.py`
- Dashboard: `src/aadhaarpulse/dashboard/app.py` (launched via `app/streamlit_app.py`)

---

## 5) Core features (what the system can do)

### 5.1 District-level Stress Index (ASSI)
AadhaarGyan computes **ASSI** at district $d$ and month $t$ as a weighted composite of operational stress components:

$$\mathrm{ASSI}_{d,t} = 0.35\,Z(\Delta \mathrm{Enrol}_{d,t}) + 0.35\,Z(\log(1+\mathrm{Updates}_{d,t})) + 0.20\,Z(\mathrm{BioPerEnrol}_{d,t}) + 0.10\,Z(\mathrm{FrictionProxy}_{d,t})$$

Where:
- $\Delta \mathrm{Enrol}_{d,t}$: month-over-month enrolment growth (smoothed/clipped)
- $\mathrm{Updates}_{d,t} = \mathrm{DemoUpdates}_{d,t} + \mathrm{BioUpdates}_{d,t}$
- $\mathrm{BioPerEnrol}_{d,t} = (\mathrm{BioUpdates}+1)/(\mathrm{Enrol}+1)$
- $\mathrm{FrictionProxy}_{d,t} = (\mathrm{DemoUpdates}+1)/(\mathrm{Enrol}+1)$
- $Z(\cdot)$: national z-score for comparability

ASSI is exported in:
- `reports/tables/district_assi_top100_latest.csv`
- `reports/tables/assi_formula.md`

### 5.2 Governance intelligence signals
Based on the governance framing in `docs/AADHAARPULSE_GOVERNANCE_FRAMING.md`, AadhaarGyan derives signals aligned to policy levers:

| Signal layer | Proxy signal (examples) | Operational interpretation | UIDAI lever |
|---|---|---|---|
| Migration | address update patterns / migration flags | mobility hotspots, transient demand | pop-up update camps, mobile vans |
| Ageing / credential maintenance | biometric refresh intensity | ageing cohorts needing refresh | scheduled biometric drives |
| Inclusion | child enrol momentum / low uptake | exclusion risk pockets | targeted outreach & drives |
| Urbanisation | demographic update mix / growth behavior | urban pull and service load | centre capacity planning |

### 5.3 Anomaly watchlist (early warning)
The pipeline flags district-month anomalies (spikes/drops), enabling a rapid watchlist for sudden operational shocks.

Dashboard view: **Anomaly watchlist** table and district drill-down.

### 5.4 Forecasting (6–12 months)
AadhaarGyan forecasts district-level volumes:
- `enrol_total`
- `demo_total`
- `bio_total`

Outputs:
- `reports/tables/district_forecast_12m.csv`
- `reports/tables/forecast_metrics.csv`

Forecast baseline metrics currently recorded (MAE):
- Enrolment MAE: **247.17**
- Demographic MAE: **1707.96**
- Biometric MAE: **1331.58**

> These are baseline evaluation numbers produced by the current modeling pipeline and should be recalculated on the full/latest dataset during deployment.

### 5.5 Intervention Planner (actionability)
The Streamlit dashboard includes an **Intervention Planner** that ranks districts using a composite *Intervention Priority Score* (built from ASSI and supporting signals) and suggests within-state resource reallocation using deficit/surplus buckets.

### 5.6 What-if Policy Simulator
AadhaarGyan supports scenario simulation for top-stress districts:

- **Add centres** scenario (capacity uplift)
- **Biometric drive** scenario (clear backlog/refresh)

Output:
- `reports/tables/what_if_top200.csv`  
Columns include `ASSI`, `assi_after_centers`, `assi_after_bio_drive`.

---

## 6) Dashboard (website) capabilities
The Streamlit dashboard (`AadhaarGyan Dashboard`) is an operational command centre:

- **Data source self-check**: detects project root + expected parquet/csv outputs
- **National overview**: KPIs, health score bar, risk cards
- **Stress hotspots**: top districts, driver breakdown
- **Trends**: national/state trends and anomaly watchlist
- **Forecasts tab**: district-level history vs forecast plot
- **What-if tab**: scenario outcomes and summary charts
- **Downloads tab**: directly export key generated CSVs

---

## 7) Scalability & performance design
AadhaarGyan is engineered for scale in three dimensions: data volume, geography, and time.

### 7.1 Data pipeline scalability
- **Batch + columnar**: curated panel persisted as **Parquet** (`district_month_panel.parquet`) for fast reads.
- **Aggregation-first**: the modeling layer operates on district-month panels rather than individual-level records.
- **Deterministic output artifacts**: pipeline generates reusable tables (`reports/tables/*.csv`) enabling stateless dashboards.

Practical scale path:
- Increase the time window (months/years) → panel grows linearly with months.
- Add features → computed on the panel using groupby/rolling transforms.
- Parallelisation option: move heavy steps (cleaning/panel build/feature compute) to scheduled jobs.

### 7.2 Dashboard scalability
- Dashboard reads Parquet and CSV outputs; interactive operations are mostly filtering + plotting.
- `st.cache_data` is used to cache file reads.
- The dashboard remains usable even if some columns are missing (defensive checks).

### 7.3 Deployment scalability
Recommended deployment patterns:
- **Offline batch job** (nightly/weekly) produces artifacts.
- **Dashboard service** only reads artifacts (no heavy training at request time).
- Optional: store artifacts in object storage (S3/Azure Blob/GCS) and mount or fetch.

---

## 8) Privacy, security, and compliance
AadhaarGyan is designed around aggregated counts and does not require individual-level identity data.

Security/privacy considerations:
- Use only aggregated district/time slices.
- Avoid publishing raw extracts; publish only derived indicators.
- Add access controls for dashboard if deployed (OIDC/SSO).
- Maintain audit logs of pipeline runs (hash inputs, store run metadata).

---

## 9) Reproducibility (how to run)
### Pipeline
The CLI orchestrates the full run:
- Module: `src/aadhaarpulse/cli.py`
- Command: `python -m aadhaarpulse.cli run-all --data-root <path>`

### Dashboard
- Entry point: `app/streamlit_app.py` → `aadhaarpulse.dashboard.app.main()`

---

## 10) Outputs produced (artifacts)
After running the pipeline, these key artifacts are generated:

- `data/processed/district_month_panel.parquet` – curated district-month panel
- `reports/tables/district_assi_top100_latest.csv` – stress leaderboard (latest month)
- `reports/tables/national_monthly_totals.csv` – national monthly totals
- `reports/tables/district_forecast_12m.csv` – 12-month district forecasts
- `reports/tables/forecast_metrics.csv` – baseline forecast evaluation metrics
- `reports/tables/what_if_top200.csv` – what-if scenario results for top 200 targets
- `reports/tables/data_health.csv` – pipeline data health summary
- `reports/tables/assi_formula.md` – ASSI documentation snippet

---

## 11) Limitations (current scope)
- The insight pack (`docs/INSIGHTS.md`) is currently a **template**; it should be populated with evidence-backed results after a full run on the final evaluation dataset.
- ASSI weights and thresholds may require calibration using UIDAI operational ground truth (queue times, center capacity, failure rates).
- Forecast metrics shown are baseline values from the current pipeline run; productionization needs robust time-split evaluation and monitoring.

---

## 12) Future roadmap
High-value next steps aligned to UIDAI operations:

1. **Capacity-aware modeling**: incorporate center counts, staffing, outage logs (if available).
2. **Monitoring & alerts**: automated alerts for anomaly spikes and high ASSI trajectories.
3. **Explainability**: driver decomposition of ASSI per district and month.
4. **Role-based access**: multi-tenant dashboard for state/district ops.
5. **Data integration** (outside hackathon scope): weather/disaster indicators, mobility proxies, event calendars.

---

## 13) One-paragraph pitch (for the report front-page)
AadhaarGyan turns aggregated UIDAI enrolment and update statistics into a district-level early-warning and planning system. Using a reproducible pipeline, it constructs a national district-month panel, computes a composite stress index (ASSI), flags anomalies, forecasts demand for 12 months, and simulates policy interventions such as adding centres or running biometric drives. The Streamlit dashboard acts as a command centre: highlighting hotspots, explaining drivers, and enabling targeted action—helping UIDAI proactively reduce backlogs, improve citizen experience, and strengthen inclusion.
