from __future__ import annotations

from pathlib import Path

import pandas as pd

from aadhaarpulse.pipelines.cleaning import clean_enrolment


def test_clean_enrolment_adds_total() -> None:
    df = pd.DataFrame(
        {
            "date": ["02-03-2025"],
            "state": ["X"],
            "district": ["Y"],
            "pincode": [123456],
            "age_0_5": [1],
            "age_5_17": [2],
            "age_18_greater": [3],
        }
    )
    out = clean_enrolment(df)
    assert int(out.loc[0, "enrol_total"]) == 6
