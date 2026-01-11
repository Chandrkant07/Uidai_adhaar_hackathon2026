from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    folder: Path
    pattern: str = "*.csv"


def _read_many_csv(folder: Path, pattern: str = "*.csv") -> pd.DataFrame:
    files = sorted(folder.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found in {folder} matching {pattern}")

    dfs: list[pd.DataFrame] = []
    for f in files:
        df = pd.read_csv(f)
        df["_source_file"] = f.name
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def load_enrolment(enrolment_dir: Path) -> pd.DataFrame:
    df = _read_many_csv(enrolment_dir)
    df["dataset"] = "enrolment"
    return df


def load_demographic(demo_dir: Path) -> pd.DataFrame:
    df = _read_many_csv(demo_dir)
    df["dataset"] = "demographic"
    return df


def load_biometric(bio_dir: Path) -> pd.DataFrame:
    df = _read_many_csv(bio_dir)
    df["dataset"] = "biometric"
    return df
