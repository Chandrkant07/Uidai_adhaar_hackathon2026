from __future__ import annotations

import pandas as pd


def _std_geo(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["state"] = out["state"].astype(str).str.strip()
    out["district"] = out["district"].astype(str).str.strip()
    out["pincode"] = pd.to_numeric(out["pincode"], errors="coerce").astype("Int64")
    return out


def _std_date(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # Raw uses dd-mm-yyyy
    out["date"] = pd.to_datetime(out["date"], format="%d-%m-%Y", errors="coerce")
    return out


def clean_enrolment(df: pd.DataFrame) -> pd.DataFrame:
    out = _std_date(_std_geo(df))

    # Ensure numeric types
    for c in ["age_0_5", "age_5_17", "age_18_greater"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0).astype("int64")

    out["enrol_total"] = out[["age_0_5", "age_5_17", "age_18_greater"]].sum(axis=1)
    return out


def _clean_update(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    out = _std_date(_std_geo(df))

    # NOTE: The demo/bio files appear truncated in header (ending with `_`).
    # We keep all numeric columns besides keys and sum them as a total update volume.
    key_cols = {"date", "state", "district", "pincode", "dataset", "_source_file"}
    num_cols = [c for c in out.columns if c not in key_cols]

    for c in num_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0).astype("int64")

    out[f"{prefix}_total"] = out[num_cols].sum(axis=1) if num_cols else 0
    return out


def clean_demographic(df: pd.DataFrame) -> pd.DataFrame:
    return _clean_update(df, prefix="demo")


def clean_biometric(df: pd.DataFrame) -> pd.DataFrame:
    return _clean_update(df, prefix="bio")


def to_district_month(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # Month-start timestamp; compatible across pandas versions
    out["month"] = out["date"].dt.to_period("M").dt.to_timestamp()
    return out
