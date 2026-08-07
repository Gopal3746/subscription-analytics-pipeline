from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "raw" / "olist"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    kaggle = shutil.which("kaggle")
    if not kaggle:
        raise SystemExit(
            "Kaggle CLI is not installed. Install it with `pip install kaggle`, authenticate it, "
            "then rerun; or download olistbr/brazilian-ecommerce manually into data/raw/olist/."
        )
    subprocess.run([
        kaggle, "datasets", "download", "-d", "olistbr/brazilian-ecommerce",
        "-p", str(DEST), "--unzip"
    ], check=True)
    print(f"Downloaded Olist dataset to {DEST}")


if __name__ == "__main__":
    main()
