# Resume-ready project bullets

**Subscription Commerce ETL & Analytics Pipeline**  
*Python, PySpark, dbt, DuckDB, SQL*

- Architected a multi-source ETL pipeline ingesting order, payment, product, catalog, and marketing data from **99,441 real e-commerce orders**, transforming observed commerce events into a clearly labeled synthetic subscription layer for churn, LTV, MRR-equivalent, and cohort-retention analysis.
- Built **16 dbt models** that standardized business logic across recurring revenue, churn, LTV, and cohort-retention marts with automated data-quality tests.
- Processed raw sources using local PySpark into Parquet, mirroring an AWS EMR/Glue-style distributed workflow and documenting an S3 → Glue/EMR → Athena migration path.
- Surfaced a modeled cycle-3 retention spread of **7.5 percentage points** across **4 customer value segments** through cohort analysis, demonstrating pipeline-to-insight ownership.

> Subscription enrollment, billing cycles, churn, LTV, MRR-equivalent, and retention are synthetic/model-derived; the underlying Olist commerce orders are real and anonymized.
