"""Cross-check resume metrics directly from source CSVs without Spark/dbt.

This is a validation path, not the production pipeline. It uses the same subscription
logic as the warehouse stage so metric claims can be independently reproduced.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import pandas as pd

from subscription_commerce.config import ARTIFACTS, RAW_OLIST, REQUIRED_OLIST
from subscription_commerce.resume_metrics import render_bullets
from subscription_commerce.subscription_logic import CustomerProfile, generate_all


def main() -> None:
    customers = pd.read_csv(RAW_OLIST / REQUIRED_OLIST["customers"]).drop_duplicates()
    orders = pd.read_csv(RAW_OLIST / REQUIRED_OLIST["orders"]).drop_duplicates()
    payments = pd.read_csv(RAW_OLIST / REQUIRED_OLIST["payments"]).drop_duplicates()
    items = pd.read_csv(RAW_OLIST / REQUIRED_OLIST["order_items"]).drop_duplicates()

    for col in ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")

    pay = payments.groupby("order_id", as_index=False)["payment_value"].sum()
    frame = (
        orders.merge(customers[["customer_id", "customer_unique_id", "customer_state"]], on="customer_id")
        .merge(pay, on="order_id", how="left")
    )
    frame = frame[(frame["order_status"] == "delivered") & frame["order_purchase_timestamp"].notna()].copy()
    frame["payment_value"] = frame["payment_value"].fillna(0.0)
    frame = frame.sort_values(["customer_unique_id", "order_purchase_timestamp"])
    frame["gap_days"] = frame.groupby("customer_unique_id")["order_purchase_timestamp"].diff().dt.days
    frame["delivery_delay_days"] = (
        (frame["order_delivered_customer_date"] - frame["order_estimated_delivery_date"])
        .dt.total_seconds().div(86400).fillna(0).clip(lower=0)
    )

    features = frame.groupby("customer_unique_id").agg(
        customer_state=("customer_state", "first"),
        first_order_date=("order_purchase_timestamp", "min"),
        order_count=("order_id", "nunique"),
        avg_order_value=("payment_value", "mean"),
        total_spend=("payment_value", "sum"),
        avg_delivery_delay_days=("delivery_delay_days", "mean"),
    ).reset_index()
    cadence = frame.loc[frame["gap_days"] > 0].groupby("customer_unique_id")["gap_days"].median()
    features = features.merge(cadence.rename("observed_cadence_days"), on="customer_unique_id", how="left")

    observed = features["observed_cadence_days"].dropna().tolist()
    fallback = int(round(statistics.median(observed))) if observed else 60
    fallback = max(30, min(120, fallback))
    q1, q2, q3 = features["total_spend"].quantile([0.25, 0.5, 0.75]).tolist()

    def segment(spend: float) -> str:
        if spend <= q1:
            return "value_1"
        if spend <= q2:
            return "value_2"
        if spend <= q3:
            return "value_3"
        return "value_4"

    profiles = []
    for row in features.itertuples(index=False):
        cadence_days = fallback if pd.isna(row.observed_cadence_days) else int(round(float(row.observed_cadence_days)))
        cadence_days = max(30, min(120, cadence_days))
        profiles.append(CustomerProfile(
            customer_unique_id=str(row.customer_unique_id),
            first_order_date=row.first_order_date.date(),
            order_count=int(row.order_count),
            avg_order_value=float(row.avg_order_value),
            total_spend=float(row.total_spend),
            avg_delivery_delay_days=float(row.avg_delivery_delay_days),
            customer_state=str(row.customer_state),
            cadence_days=cadence_days,
            value_segment=segment(float(row.total_spend)),
        ))

    cycles = pd.DataFrame(generate_all(profiles))
    cohort = cycles[(cycles["cycle_number"] == 1) & (cycles["renewed"] == 1)].groupby("value_segment")["subscription_id"].nunique()
    retained = cycles[(cycles["cycle_number"] == 3) & (cycles["renewed"] == 1)].groupby("value_segment")["subscription_id"].nunique()
    retention = (retained / cohort).fillna(0.0)
    per_sub = cycles.groupby("subscription_id").agg(
        churned=("churned_this_cycle", "max"),
        ltv=("billing_amount", "sum"),
    )

    metrics = {
        "real_orders": int(len(orders)),
        "real_payment_records": int(len(payments)),
        "real_order_items": int(len(items)),
        "synthetic_subscribers": int(cycles["subscription_id"].nunique()),
        "synthetic_billing_cycles": int(len(cycles)),
        "customer_segments": int(len(retention)),
        "retention_cycle": 3,
        "retention_variance_pct_points": round(float((retention.max() - retention.min()) * 100), 1),
        "best_segment": str(retention.idxmax()),
        "best_segment_retention_pct": round(float(retention.max() * 100), 1),
        "worst_segment": str(retention.idxmin()),
        "worst_segment_retention_pct": round(float(retention.min() * 100), 1),
        "synthetic_churn_rate_pct": round(float(per_sub["churned"].mean() * 100), 1),
        "synthetic_avg_ltv_brl": round(float(per_sub["ltv"].mean()), 2),
        "fallback_cadence_days": fallback,
        "validation_path": "direct_csv_crosscheck",
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "resume_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (ARTIFACTS / "resume_bullets.md").write_text(render_bullets(metrics), encoding="utf-8")
    retention.rename("cycle3_retention_rate").reset_index().to_csv(ARTIFACTS / "segment_retention.csv", index=False)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
