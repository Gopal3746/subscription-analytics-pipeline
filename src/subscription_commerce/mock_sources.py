from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .config import RAW_MOCK, RAW_OLIST, ensure_dirs
from .hash_utils import stable_unit_interval


def month_iter(start_year=2016, start_month=9, end_year=2018, end_month=10):
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        yield date(year, month, 1)
        month += 1
        if month == 13:
            year += 1
            month = 1


def build_marketing_spend(path: Path) -> int:
    states = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF"]
    channels = ["paid_search", "social", "affiliate", "email"]
    rows = []
    for month in month_iter():
        for state in states:
            for channel in channels:
                u = stable_unit_interval(month.isoformat(), state, channel)
                base = {"paid_search": 8000, "social": 5000, "affiliate": 3500, "email": 1800}[channel]
                rows.append({
                    "month": month.isoformat(),
                    "customer_state": state,
                    "channel": channel,
                    "spend_brl": round(base * (0.75 + 0.5 * u), 2),
                    "impressions": int(50000 + 150000 * u),
                    "clicks": int(1000 + 9000 * u),
                })
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def build_catalog_overrides(path: Path) -> int:
    source = RAW_OLIST / "olist_products_dataset.csv"
    rows = []
    if source.exists():
        with source.open(newline="", encoding="utf-8") as f:
            for rec in csv.DictReader(f):
                pid = rec["product_id"]
                u = stable_unit_interval(pid, "catalog")
                rows.append({
                    "product_id": pid,
                    "catalog_tier": "premium" if u > 0.82 else "standard" if u > 0.28 else "value",
                    "subscription_eligible": int(u > 0.18),
                    "margin_band": "high" if u > 0.70 else "mid" if u > 0.32 else "low",
                })
    else:
        rows = [
            {"product_id": "sample_product_001", "catalog_tier": "standard", "subscription_eligible": 1, "margin_band": "mid"},
            {"product_id": "sample_product_002", "catalog_tier": "premium", "subscription_eligible": 1, "margin_band": "high"},
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    ensure_dirs()
    print(f"marketing rows={build_marketing_spend(RAW_MOCK / 'marketing_spend.csv')}")
    print(f"catalog rows={build_catalog_overrides(RAW_MOCK / 'catalog_overrides.csv')}")


if __name__ == "__main__":
    main()
