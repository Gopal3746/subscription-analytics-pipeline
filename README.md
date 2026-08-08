# Subscription Commerce ETL & Analytics Pipeline

A production-style analytics engineering project that transforms a real, anonymized e-commerce dataset through a multi-source Spark/dbt pipeline, then layers an explicitly **synthetic recurring-billing model** on top for subscription-style analytics.

**Stack:** Python · PySpark · dbt · DuckDB · SQL

## What this demonstrates

- Multi-source ingestion across real Olist commerce data plus two separately generated mock business sources.
- Local PySpark normalization into parquet, using the same DataFrame API used on EMR/Glue Spark.
- DuckDB warehouse loading and dbt staging/intermediate/mart transformations.
- Reproducible subscription-style churn, LTV, MRR-equivalent, and cohort-retention analysis.
- Automated tests and a metrics artifact that fills the resume placeholders from an actual run.

## Data provenance and honesty boundary

The base dataset is the **Olist Brazilian E-Commerce Public Dataset**, containing anonymized real commercial orders from 2016–2018. Olist itself is **not** a subscription dataset.

Dataset: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce  
The repository does not commit the raw dataset; download it separately and follow the dataset license/terms.

This repository keeps two concepts separate:

- **Observed:** customers, orders, items, payments, products, reviews, purchase timestamps.
- **Synthetic/model-derived:** subscription enrollment, billing cycles, renewal/churn events, LTV, MRR-equivalent, and retention.

The synthetic subscription layer is deterministic and is generated from observed purchase cadence, spend, order frequency, delivery performance, and geography. It must never be described as real Olist subscription data.

## Architecture

```text
Olist CSVs --------------------┐
                               ├─> local PySpark ─> bronze parquet ─> DuckDB raw
Mock marketing spend ---------┤                                      │
Mock catalog attributes ------┘                                      v
                                                                dbt staging
                                                                     │
                                                                     v
                                                           order/customer facts
                                                                     │
                                                                     v
                                                     synthetic billing-cycle facts
                                                                     │
                                      ┌──────────────────────────────┼────────────────────────────┐
                                      v                              v                            v
                               recurring KPIs                 cohort retention                  LTV
                                      └──────────────────────────────┼────────────────────────────┘
                                                                     v
                                                          resume_metrics.json
```

## AWS production mapping

| Local implementation | Production analogue |
|---|---|
| `data/raw/` | Amazon S3 raw zone |
| PySpark local mode | AWS Glue Spark / EMR Serverless |
| Parquet bronze files | S3 bronze/curated parquet |
| DuckDB | Athena/Glue Catalog or analytical warehouse |
| dbt-duckdb | dbt-athena / dbt-redshift |
| Python CLI | Step Functions / MWAA / Glue Workflows |

The point is not to claim production AWS deployment. The repository shows how the local Spark and dbt logic would map to managed AWS services without requiring a cloud bill.

## Repository layout

```text
src/subscription_commerce/
  cli.py                   # end-to-end orchestration
  config.py                # paths + required files
  hash_utils.py            # deterministic pseudo-random decisions
  mock_sources.py          # marketing spend + catalog sources
  spark_ingest.py          # PySpark bronze transforms
  warehouse.py             # DuckDB raw loading + synthetic cycle generation
  subscription_logic.py    # transparent recurring-cycle model
  resume_metrics.py        # computes exact resume placeholders

dbt/models/
  staging/                  # source standardization
  intermediate/             # order/customer facts
  marts/                    # KPI, LTV, cohort, segment, marketing marts
dbt/tests/                  # custom data-quality assertions
scripts/
  download_olist.py
  verify_project.py
dashboard/
  app.py                   # Streamlit BI layer over dbt marts
artifacts/
  spark_ingest_audit.json   # generated
  resume_metrics.json       # generated
  resume_bullets.md         # generated with zero placeholders
```

## Required Olist files

Place these in `data/raw/olist/`:

- `olist_customers_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_products_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `product_category_name_translation.csv`

## Run locally

### 1. Setup

```bash
make setup
```

PySpark requires Java. Java 11 or Java 17 is recommended for Spark 3.5.

### 2. Get Olist data

If your Kaggle CLI is authenticated:

```bash
make data
```

Otherwise download `olistbr/brazilian-ecommerce` from Kaggle and copy the seven required CSVs into `data/raw/olist/`.

### 3. Run everything

```bash
make run
```

Or run stages individually:

```bash
make mocks
make spark
make warehouse
make dbt
make metrics
make test
make verify
```

### 4. Get the exact resume values

```bash
cat artifacts/resume_metrics.json
cat artifacts/resume_bullets.md
```

`resume_bullets.md` is generated from warehouse results, so it contains no guessed `[X]` values.

### 5. Launch the BI dashboard

```bash
make dashboard
```

The dashboard reads only dbt marts from DuckDB and shows KPI cards, segment retention curves, monthly cohorts, and observed revenue vs. mock marketing spend.

## Synthetic subscription methodology

1. Reconstruct customer histories with Olist `customer_unique_id`.
2. Infer purchase cadence from repeat customers; clamp inferred cadence to 30–120 days.
3. Split customers into four observed-spend quartiles: `value_1`, `value_2`, `value_3`, `value_4`.
4. Derive deterministic subscription enrollment from purchase frequency, spend, and delivery delay.
5. Generate up to six recurring billing cycles using stable SHA-256 decisions, not mutable random seeds.
6. Set each synthetic billing amount from the customer's observed average order value.
7. Calculate churn, realized synthetic LTV, cohort retention, and value-segment retention from those modeled cycles.

Value segments are used only for downstream analysis; renewal probability is modeled from continuous observed features rather than hard-coded segment labels, so the segment spread is an analytical result of the simulation rather than a direct segment rule.

## dbt models

### Staging

Standardizes raw types and naming for customers, orders, order items, payments, products, reviews, marketing spend, catalog attributes, and subscription cycles.

### Intermediate

- `int_order_facts`: one row per order with payment and line-item aggregates.
- `int_customer_features`: observed customer order count, revenue, AOV, state, and first order date.

### Marts

- `mart_subscription_kpis`: synthetic subscribers, churn rate, recurring revenue, average LTV.
- `mart_cohort_retention`: retention curves by enrollment month and cycle number.
- `mart_segment_retention`: retention curves across four customer value segments.
- `mart_customer_ltv`: synthetic LTV and active cycles at subscriber grain.
- `mart_marketing_efficiency`: observed commerce revenue vs. mock marketing spend by month/state.

## What fills the resume placeholders

After a successful full run, `artifacts/resume_metrics.json` stores:

- `real_orders`: exact Olist order rows ingested after Spark deduplication.
- `real_payment_records`: exact Olist payment rows ingested.
- `real_order_items`: exact Olist line items ingested.
- `customer_segments`: number of eligible value segments in the retention comparison.
- `retention_variance_pct_points`: highest minus lowest cycle-3 retention, in percentage points.
- `best_segment` / `worst_segment`: segments producing the spread.
- `synthetic_subscribers` / `synthetic_billing_cycles`: scale of the modeled layer.

The generated resume bullet uses **orders** as the transaction count because that is the cleanest business-grain definition of a transaction. Payment records and line items remain available as supporting scale metrics.

## Resume-ready wording

The generated file will follow this structure:

> **Subscription Commerce ETL & Analytics Pipeline** — *Python, PySpark, dbt, DuckDB, SQL*  
> - Architected a multi-source ETL pipeline ingesting order, payment, product, catalog, and marketing data from **{real_orders} real e-commerce orders**, transforming observed commerce events into a clearly labeled synthetic subscription layer for churn, LTV, MRR-equivalent, and cohort-retention analysis.  
> - Built **16 dbt models** that standardized business logic across recurring revenue, churn, LTV, and cohort-retention marts with automated data-quality tests.  
> - Processed raw sources using local PySpark into Parquet, mirroring an AWS EMR/Glue-style distributed workflow and documenting an S3 → Glue/EMR → Athena migration path.  
> - Surfaced a modeled cycle-3 retention spread of **{retention_variance_pct_points} percentage points** across **{customer_segments} customer value segments** through cohort analysis, demonstrating pipeline-to-insight ownership.

## Reference validation snapshot

A direct-source cross-check using the same deterministic subscription logic produced:

- **99,441** real Olist orders
- **103,886** real payment records
- **112,650** real order-item records
- **16,955** modeled subscribers and **62,125** modeled billing-cycle rows
- cycle-3 retention from **43.3%** in the lowest observed-spend quartile to **50.8%** in the highest, a **7.5 percentage-point spread across 4 segments**

These subscription results are synthetic/model-derived. Run `make run` on the canonical Olist files to regenerate the warehouse outputs, and `python scripts/crosscheck_metrics.py` to independently cross-check the resume metrics directly from the source CSVs.

## Validation

Unit tests cover deterministic hashing and recurring-cycle behavior. dbt tests cover key uniqueness/nullability, negative payment/billing amounts, duplicate subscription cycles, and retention bounds.

```bash
make test
make verify
```

A portfolio-ready run must produce the Spark audit, warehouse, resume metrics, and fully substituted resume bullets.
