# Suggested GitHub Repository Structure

```
aadhaarpulse/
  README.md
  pyproject.toml
  src/
    aadhaarpulse/
      __init__.py
      cli.py
      config.py
      pipelines/
        io.py
        cleaning.py
        panel.py
        run_all.py
      features/
        assi.py
        signals.py
      models/
        forecasting.py
      simulator/
        what_if.py
  data/
    raw/           # optional local copy / symlink of the official CSVs
    interim/
    processed/
  reports/
    figures/
    tables/
  docs/
    AADHAARPULSE_GOVERNANCE_FRAMING.md
    PPT_OUTLINE_15_SLIDES.md
    UIDAI_SUBMISSION_PDF_STRUCTURE.md
    JURY_PITCH_60_SECONDS.md
    INSIGHTS.md
  tests/
    test_smoke_pipeline.py
```

**Why this wins:** clean separation between ingestion, feature engineering, modeling, policy simulation, and final narrative deliverables.
