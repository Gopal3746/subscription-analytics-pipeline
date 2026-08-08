# Resume Template

**Subscription Commerce ETL & Analytics Pipeline**  
*Python, PySpark, dbt, DuckDB, SQL*

- Architected a multi-source ETL pipeline ingesting order, payment, product, catalog, and marketing data from **[REAL_ORDERS] real e-commerce orders**, transforming observed commerce events into a clearly labeled synthetic subscription layer for churn, LTV, MRR-equivalent, and cohort-retention analysis.
- Built **16 dbt models** that standardized business logic across recurring revenue, churn, LTV, and cohort-retention marts with automated data-quality tests.
- Processed raw sources using local PySpark into parquet, mirroring an AWS EMR/Glue-style distributed workflow and documenting an S3 → Glue/EMR → Athena migration path.
- Surfaced a modeled cycle-3 retention spread of **[RETENTION_VARIANCE_PP] percentage points** across **[CUSTOMER_SEGMENTS] customer value segments** through cohort analysis, demonstrating pipeline-to-insight ownership.

Run `make run`. The final values are written to `artifacts/resume_bullets.md`.
