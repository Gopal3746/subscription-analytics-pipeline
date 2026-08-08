# AWS deployment mapping

| Local | AWS target | Main change |
|---|---|---|
| raw CSV directory | S3 raw prefix | replace local paths with S3 URIs |
| PySpark local mode | Glue Spark / EMR Serverless | externalize Spark master and runtime config |
| bronze parquet | S3 bronze prefix | write parquet to S3 |
| DuckDB source catalog | Glue Catalog + Athena | catalog parquet and retarget dbt |
| dbt-duckdb | dbt-athena / dbt-redshift | update adapter/profile |
| local CLI | Step Functions / MWAA | split stages into managed jobs |
| JSON audit | CloudWatch/S3 | emit operational metrics centrally |

## Production controls to add

- IAM least-privilege roles per job.
- S3 versioning/lifecycle policies.
- Incremental processing by order/billing date.
- Glue Data Quality or equivalent source contracts.
- CloudWatch alarms for failed jobs and row-count drift.
- Secrets Manager for credentials.
