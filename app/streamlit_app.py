"""Streamlit entrypoint.

This repo uses a `src/` layout, so running Streamlit directly from the repo
won't always find the `aadhaarpulse` package unless the project is installed
(e.g., `pip install -e .`).

To keep hackathon demos frictionless, we add `<repo>/src` to `sys.path` as a
safe fallback when running from source.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


_ensure_src_on_path()

from aadhaarpulse.dashboard.app import main

if __name__ == "__main__":
    main()
