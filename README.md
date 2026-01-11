# AadhaarPulse – India’s Identity & Service Intelligence Engine

This repository implements a national-scale analytics + forecasting system built **only** on the official UIDAI hackathon datasets:

- Aadhaar Enrolment (daily, PIN-level)
- Aadhaar Demographic Updates (daily, PIN-level)
- Aadhaar Biometric Updates (daily, PIN-level)

It produces:
- A harmonised time–geo panel dataset
- District/PIN signals for migration, urbanisation, ageing, inclusion, and infrastructure stress
- Anomaly detection and a decision metric: **Aadhaar Service Stress Index (ASSI)**
- District-level forecasts for the next 6–12 months
- A light-weight policy “what-if” simulator for staffing/centre allocation and special drives

## Quick start (Windows / PowerShell)

1. Create a venv and install:

```powershell
cd d:\Uidai_adhar\aadhaarpulse
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .[dev]
```

2. Run the end-to-end pipeline:

```powershell
python -m aadhaarpulse.cli run-all --data-root d:\Uidai_adhar
```

Outputs go to `data/processed/`, `reports/tables/`, and `reports/figures/`.

## Project layout

- `src/aadhaarpulse/` – pipeline and modeling code
- `data/raw/` – optional copy/symlink of raw CSVs (we read from `--data-root` by default)
- `data/processed/` – curated datasets (parquet)
- `reports/` – figures and tables for PPT/PDF
- `docs/` – hackathon write-up, PPT outline, PDF structure

## Notes

- We assume **aggregated** data (no personal data).
- Dates in raw files are `dd-mm-yyyy`.
