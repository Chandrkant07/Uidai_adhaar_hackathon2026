# AadhaarGyan – India’s Identity & Service Intelligence Engine (UIDAI Hackathon 2026)

**Team Lead**: Chandrkant07 | **Branch**: Main

---

## 🚀 The Vision
AadhaarGyan transforms **aggregated Aadhaar enrolment and update data** into a national-scale **early-warning system**. Instead of reacting to centre-level stress, UIDAI can now **predict** service demand, **detect** migration hotspots, and **prevent** exclusions using our proprietary **Aadhaar Service Stress Index (ASSI)**.

> *"We don't just show data. We tell UIDAI where to send the next mobile enrolment van."*

---

## 🔑 Key Capabilities

### 1. **Aadhaar Service Stress Index (ASSI)**
A unified district-level metric (0–100) that fuses:
- **Enrolment Shocks**: Sudden deviations in onboarding.
- **Update Load**: Weighted volume of demographic + biometric corrections.
- **Biometric Pressure**: Ageing cohorts reflecting high refresh demand.
- **Friction Signals**: Repeated updates per enrolment.

### 2. **National Control Room Dashboard**
A Streamlit-powered command center featuring:
- **Intervention Planner**: Top-10 districts requiring immediate action.
- **Anomaly Watchlist**: AI-detected spikes in migration or update failures.
- **What-If Policy Simulator**: "If we add 5 centers here, ASSI drops by 12 points."
- **Forecasts**: 12-month demand prediction for every district.

### 3. **Governance Intelligence Layers**
- **Migration Signal**: Tracking workforce mobility via address updates.
- **Inclusion Radar**: Monitoring 0–5 age group enrolment rates.
- **Infrastructure Stress**: Load intensity per active PIN code.

---

## 🛠️ Tech Stack & Architecture
- **Core Pipeline**: Python 3.10+, Pandas (Panel construction).
- **Forecasting**: Gradient-boosted trees (Scikit-Learn/HistGradientBoosting) with recursive multi-step prediction.
- **Anomaly Detection**: Robust MAD (Median Absolute Deviation) scoring.
- **Dashboard**: Streamlit + Plotly interactive charts.
- **Data**: Official UIDAI Enrolment, Demographic, and Biometric datasets (aggregated).

---

## ⚡ Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/Chandrkant07/Uidai_adhaar_hackathon2026.git
cd Uidai_adhaar_hackathon2026/aadhaarpulse
pip install -e .[dev]
```

### 2. Run the Full Pipeline
Ingests raw CSVs, harmonises data, computes ASSI, and generates forecasts.
```bash
# Point --data-root to the folder containing api_data_* folders
python -m aadhaarpulse.cli run-all --data-root /path/to/raw/data
```
*Outputs are saved to `data/processed/` and `reports/tables/`.*

### 3. Launch the Dashboard
```bash
streamlit run app/streamlit_app.py
```
*Access at http://localhost:8501*

---

## 📊 Repository Structure
```
aadhaarpulse/
├── src/aadhaarpulse/
│   ├── dashboard/       # Streamlit App & visualisations
│   ├── features/        # ASSI, Migration/Urbanisation signals
│   ├── models/          # Forecasting & Anomaly detection
│   ├── pipelines/       # ETL & Panel generation
│   └── simulator/       # What-if policy engine
├── docs/                # PPT Outline, Governance Framing, Insights
├── reports/             # Generated csv tables & figures
├── tests/               # Automated pipeline tests
└── pyproject.toml       # Dependencies
```

---

## 🏆 Impact Metrics
- **reduce wait-times** in high-stress districts by proactive resource allocation.
- **improve success rates** by targeting high-failure anomaly zones.
- **enhance inclusion** by flagging districts with low child enrolment momentum.

---

## 📜 License
This project is submitted for the UIDAI Hackathon 2026. Code is open for evaluation.
