from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataPaths:
    """Paths to the three UIDAI datasets.

    We expect the workspace layout provided in the prompt:

    <data_root>/api_data_aadhar_enrolment/*.csv
    <data_root>/api_data_aadhar_demographic/*.csv
    <data_root>/api_data_aadhar_biometric/*.csv
    """

    data_root: Path

    @property
    def enrolment_dir(self) -> Path:
        return self.data_root / "api_data_aadhar_enrolment"

    @property
    def demographic_dir(self) -> Path:
        return self.data_root / "api_data_aadhar_demographic"

    @property
    def biometric_dir(self) -> Path:
        return self.data_root / "api_data_aadhar_biometric"


@dataclass(frozen=True)
class OutputPaths:
    project_root: Path

    @property
    def interim_dir(self) -> Path:
        return self.project_root / "data" / "interim"

    @property
    def processed_dir(self) -> Path:
        return self.project_root / "data" / "processed"

    @property
    def tables_dir(self) -> Path:
        return self.project_root / "reports" / "tables"

    @property
    def figures_dir(self) -> Path:
        return self.project_root / "reports" / "figures"
