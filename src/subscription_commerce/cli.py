from __future__ import annotations

import argparse
import os
import subprocess
import sys

from .config import DBT_DIR, ROOT, missing_olist_files


def run_cmd(args, cwd=None):
    print("+", " ".join(map(str, args)))
    subprocess.run(args, cwd=cwd, check=True)


def run_pipeline() -> None:
    missing = missing_olist_files()
    if missing:
        raise SystemExit(
            "Missing Olist CSVs:\n  - " + "\n  - ".join(missing)
            + "\n\nRun `python scripts/download_olist.py` or place the files in data/raw/olist/."
        )
    py = sys.executable
    run_cmd([py, "-m", "subscription_commerce.mock_sources"], cwd=ROOT)
    run_cmd([py, "-m", "subscription_commerce.spark_ingest"], cwd=ROOT)
    run_cmd([py, "-m", "subscription_commerce.warehouse"], cwd=ROOT)
    dbt = os.path.join(os.path.dirname(py), "dbt")
    run_cmd([dbt, "build", "--profiles-dir", "."], cwd=DBT_DIR)
    run_cmd([py, "-m", "subscription_commerce.resume_metrics"], cwd=ROOT)
    run_cmd([py, "scripts/verify_project.py"], cwd=ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Subscription Commerce ETL")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="Run the complete local pipeline")
    sub.add_parser("metrics", help="Regenerate resume metrics")
    args = parser.parse_args()
    if args.command == "run":
        run_pipeline()
    else:
        from .resume_metrics import main as metrics_main
        metrics_main()


if __name__ == "__main__":
    main()
