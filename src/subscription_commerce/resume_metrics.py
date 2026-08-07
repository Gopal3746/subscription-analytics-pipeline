from __future__ import annotations

import json


from .config import ARTIFACTS, WAREHOUSE


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


def calculate(con) -> dict:
    real_orders = int(scalar(con, "select count(*) from raw.orders"))
    real_payments = int(scalar(con, "select count(*) from raw.payments"))
    real_items = int(scalar(con, "select count(*) from raw.order_items"))
    subscribers = int(scalar(con, "select count(distinct subscription_id) from raw.synthetic_subscription_cycles"))
    cycles = int(scalar(con, "select count(*) from raw.synthetic_subscription_cycles"))

    segment_rows = con.execute(r'''
      with cohorts as (
        select value_segment, count(distinct subscription_id) as cohort_size
        from raw.synthetic_subscription_cycles
        where cycle_number = 1 and renewed = 1
        group by 1
      ), retained as (
        select value_segment, count(distinct subscription_id) as retained_cycle3
        from raw.synthetic_subscription_cycles
        where cycle_number = 3 and renewed = 1
        group by 1
      )
      select c.value_segment, c.cohort_size, coalesce(r.retained_cycle3, 0)
      from cohorts c left join retained r using(value_segment)
      order by 1
    ''').fetchall()
    retention = [(segment, retained / cohort) for segment, cohort, retained in segment_rows if cohort >= 50]
    if len(retention) < 2:
        raise RuntimeError("Not enough eligible segments to calculate retention variance.")
    best = max(retention, key=lambda x: x[1])
    worst = min(retention, key=lambda x: x[1])
    spread_pp = round((best[1] - worst[1]) * 100, 1)

    churn_rate = float(scalar(con, r'''
      select avg(ever_churned) from (
        select subscription_id, max(churned_this_cycle) as ever_churned
        from raw.synthetic_subscription_cycles group by 1
      )
    '''))
    avg_ltv = float(scalar(con, r'''
      select avg(ltv) from (
        select subscription_id, sum(billing_amount) as ltv
        from raw.synthetic_subscription_cycles group by 1
      )
    '''))

    return {
        "real_orders": real_orders,
        "real_payment_records": real_payments,
        "real_order_items": real_items,
        "synthetic_subscribers": subscribers,
        "synthetic_billing_cycles": cycles,
        "customer_segments": len(retention),
        "retention_cycle": 3,
        "retention_variance_pct_points": spread_pp,
        "best_segment": best[0],
        "best_segment_retention_pct": round(best[1] * 100, 1),
        "worst_segment": worst[0],
        "worst_segment_retention_pct": round(worst[1] * 100, 1),
        "synthetic_churn_rate_pct": round(churn_rate * 100, 1),
        "synthetic_avg_ltv_brl": round(avg_ltv, 2),
    }


def render_bullets(m: dict) -> str:
    return f'''# Resume-ready project bullets

**Subscription Commerce ETL & Analytics Pipeline**  
*Python, PySpark, dbt, DuckDB, SQL*

- Architected a multi-source ETL pipeline ingesting order, payment, product, catalog, and marketing data from **{m['real_orders']:,} real e-commerce orders**, transforming observed commerce events into a clearly labeled synthetic subscription layer for churn, LTV, MRR-equivalent, and cohort-retention analysis.
- Built **16 dbt models** that standardized business logic across recurring revenue, churn, LTV, and cohort-retention marts with automated data-quality tests.
- Processed raw sources using local PySpark into Parquet, mirroring an AWS EMR/Glue-style distributed workflow and documenting an S3 → Glue/EMR → Athena migration path.
- Surfaced a modeled cycle-3 retention spread of **{m['retention_variance_pct_points']} percentage points** across **{m['customer_segments']} customer value segments** through cohort analysis, demonstrating pipeline-to-insight ownership.

> Subscription enrollment, billing cycles, churn, LTV, MRR-equivalent, and retention are synthetic/model-derived; the underlying Olist commerce orders are real and anonymized.
'''


def main() -> None:
    import duckdb
    if not WAREHOUSE.exists():
        raise SystemExit("Warehouse not found. Run the pipeline first.")
    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    metrics = calculate(con)
    con.close()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "resume_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (ARTIFACTS / "resume_bullets.md").write_text(render_bullets(metrics), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print("wrote artifacts/resume_metrics.json and artifacts/resume_bullets.md")


if __name__ == "__main__":
    main()
