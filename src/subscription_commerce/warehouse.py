from __future__ import annotations

import statistics

import duckdb

from .config import BRONZE, WAREHOUSE, ensure_dirs
from .subscription_logic import CustomerProfile, generate_all


def load_bronze(con: duckdb.DuckDBPyConnection) -> None:
    tables = [
        "customers", "orders", "order_items", "payments", "products", "reviews",
        "category_translation", "marketing_spend", "catalog_overrides",
    ]
    con.execute("create schema if not exists raw")
    for table in tables:
        glob = (BRONZE / table / "*.parquet").as_posix()
        con.execute(f"create or replace table raw.{table} as select * from read_parquet('{glob}')")
        count = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
        print(f"loaded raw.{table}: {count:,}")


def customer_features(con: duckdb.DuckDBPyConnection):
    return con.execute(r'''
    with pay as (
      select order_id, sum(cast(payment_value as double)) as payment_value
      from raw.payments group by 1
    ), customer_orders as (
      select
        c.customer_unique_id,
        c.customer_state,
        o.order_id,
        cast(o.order_purchase_timestamp as timestamp) as purchased_at,
        cast(o.order_delivered_customer_date as timestamp) as delivered_at,
        cast(o.order_estimated_delivery_date as timestamp) as estimated_at,
        coalesce(p.payment_value, 0) as order_value
      from raw.orders o
      join raw.customers c using(customer_id)
      left join pay p using(order_id)
      where o.order_status = 'delivered'
        and o.order_purchase_timestamp is not null
    ), gaps as (
      select *,
        date_diff('day', lag(purchased_at) over(partition by customer_unique_id order by purchased_at), purchased_at) as gap_days
      from customer_orders
    )
    select
      customer_unique_id,
      any_value(customer_state) as customer_state,
      min(cast(purchased_at as date)) as first_order_date,
      count(distinct order_id) as order_count,
      avg(order_value) as avg_order_value,
      sum(order_value) as total_spend,
      avg(greatest(coalesce(date_diff('day', estimated_at, delivered_at), 0), 0)) as avg_delivery_delay_days,
      median(gap_days) filter(where gap_days is not null and gap_days > 0) as observed_cadence_days
    from gaps
    group by 1
    ''').fetchdf()


def profiles_from_frame(df):
    cadences = [float(x) for x in df["observed_cadence_days"].dropna().tolist() if float(x) > 0]
    fallback_cadence = int(round(statistics.median(cadences))) if cadences else 60
    fallback_cadence = max(30, min(120, fallback_cadence))
    q1, q2, q3 = [float(x) for x in df["total_spend"].quantile([0.25, 0.5, 0.75]).tolist()]

    def segment(spend):
        spend = float(spend)
        if spend <= q1:
            return "value_1"
        if spend <= q2:
            return "value_2"
        if spend <= q3:
            return "value_3"
        return "value_4"

    profiles = []
    for row in df.itertuples(index=False):
        observed = row.observed_cadence_days
        cadence = fallback_cadence if observed is None or str(observed) == "nan" else int(round(float(observed)))
        cadence = max(30, min(120, cadence))
        profiles.append(CustomerProfile(
            customer_unique_id=str(row.customer_unique_id),
            first_order_date=row.first_order_date,
            order_count=int(row.order_count),
            avg_order_value=float(row.avg_order_value or 0.0),
            total_spend=float(row.total_spend or 0.0),
            avg_delivery_delay_days=float(row.avg_delivery_delay_days or 0.0),
            customer_state=str(row.customer_state or "UNKNOWN"),
            cadence_days=cadence,
            value_segment=segment(row.total_spend),
        ))
    return profiles, fallback_cadence


def load_subscription_cycles(con, rows):
    con.execute("create schema if not exists raw")
    con.execute("drop table if exists raw.synthetic_subscription_cycles")
    con.execute(r'''
      create table raw.synthetic_subscription_cycles (
        subscription_id varchar,
        customer_unique_id varchar,
        cycle_number integer,
        billing_date date,
        billing_amount double,
        renewed integer,
        churned_this_cycle integer,
        customer_state varchar,
        value_segment varchar,
        cadence_days integer
      )
    ''')
    if rows:
        con.executemany(
            "insert into raw.synthetic_subscription_cycles values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [[r[k] for k in [
                "subscription_id", "customer_unique_id", "cycle_number", "billing_date",
                "billing_amount", "renewed", "churned_this_cycle", "customer_state",
                "value_segment", "cadence_days"
            ]] for r in rows],
        )


def main() -> None:
    ensure_dirs()
    if not (BRONZE / "orders").exists():
        raise SystemExit("Bronze data missing. Run PySpark ingestion first.")
    con = duckdb.connect(str(WAREHOUSE))
    load_bronze(con)
    df = customer_features(con)
    profiles, fallback = profiles_from_frame(df)
    cycles = generate_all(profiles)
    load_subscription_cycles(con, cycles)
    print(
        f"synthetic subscribers={len({r['subscription_id'] for r in cycles}):,}; "
        f"billing cycles={len(cycles):,}; fallback cadence={fallback} days"
    )
    con.close()


if __name__ == "__main__":
    main()
