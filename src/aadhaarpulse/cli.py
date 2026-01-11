from __future__ import annotations

import argparse
from pathlib import Path

from aadhaarpulse.pipelines.run_all import run_all


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aadhaarpulse", description="AadhaarPulse pipeline runner")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run-all", help="Run end-to-end pipeline")
    run.add_argument("--data-root", type=Path, required=True, help="Folder containing api_data_*")
    run.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Project root (default: repo root)",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    if args.cmd == "run-all":
        run_all(data_root=args.data_root, project_root=args.project_root)


if __name__ == "__main__":
    main()
