from __future__ import annotations

import json
from pathlib import Path

from .config import ARTIFACTS, BRONZE, RAW_MOCK, RAW_OLIST, REQUIRED_OLIST, ensure_dirs, missing_olist_files


def get_spark():
    from pyspark.sql import SparkSession
    return (
        SparkSession.builder.appName("subscription-commerce-etl")
        .master("local[*]")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )


def write_csv_as_parquet(spark, src: Path, dst: Path, date_columns=()):
    from pyspark.sql import functions as F
    df = spark.read.option("header", True).option("inferSchema", True).csv(str(src))
    for col in date_columns:
        if col in df.columns:
            df = df.withColumn(col, F.to_timestamp(F.col(col)))
    df = df.dropDuplicates()
    dst.mkdir(parents=True, exist_ok=True)
    df.write.mode("overwrite").parquet(str(dst))
    return df.count(), len(df.columns)


def main() -> None:
    ensure_dirs()
    missing = missing_olist_files()
    if missing:
        raise SystemExit("Missing Olist files: " + ", ".join(missing))
    spark = get_spark()
    specs = {
        "customers": (RAW_OLIST / REQUIRED_OLIST["customers"], ()),
        "orders": (RAW_OLIST / REQUIRED_OLIST["orders"], (
            "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
            "order_delivered_customer_date", "order_estimated_delivery_date")),
        "order_items": (RAW_OLIST / REQUIRED_OLIST["order_items"], ("shipping_limit_date",)),
        "payments": (RAW_OLIST / REQUIRED_OLIST["payments"], ()),
        "products": (RAW_OLIST / REQUIRED_OLIST["products"], ()),
        "reviews": (RAW_OLIST / REQUIRED_OLIST["reviews"], ("review_creation_date", "review_answer_timestamp")),
        "category_translation": (RAW_OLIST / REQUIRED_OLIST["category_translation"], ()),
        "marketing_spend": (RAW_MOCK / "marketing_spend.csv", ()),
        "catalog_overrides": (RAW_MOCK / "catalog_overrides.csv", ()),
    }
    audit = {}
    for name, (src, date_cols) in specs.items():
        if not src.exists():
            raise SystemExit(f"Missing input {src}; run mock source generation first.")
        rows, cols = write_csv_as_parquet(spark, src, BRONZE / name, date_cols)
        audit[name] = {"rows": rows, "columns": cols, "source": src.name}
        print(f"bronze {name}: rows={rows:,} cols={cols}")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "spark_ingest_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    spark.stop()


if __name__ == "__main__":
    main()
