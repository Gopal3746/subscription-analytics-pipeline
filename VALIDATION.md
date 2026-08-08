# Validation snapshot

This project has two validation paths:

1. **Pipeline path:** PySpark → Parquet → DuckDB → dbt → generated resume metrics.
2. **Independent cross-check:** `scripts/crosscheck_metrics.py` recomputes the resume metrics directly from source CSVs using the same deterministic subscription logic.

## Reference cross-check results

| Metric | Result | Provenance |
|---|---:|---|
| Real orders | 99,441 | observed Olist order rows |
| Real payment records | 103,886 | observed Olist payment rows |
| Real order items | 112,650 | observed Olist line-item rows |
| Modeled subscribers | 16,955 | synthetic recurring layer |
| Modeled billing-cycle rows | 62,125 | synthetic recurring layer |
| Cycle-3 retention — lowest value quartile | 43.3% | synthetic/model-derived |
| Cycle-3 retention — highest value quartile | 50.8% | synthetic/model-derived |
| Cycle-3 retention spread | 7.5 percentage points | synthetic/model-derived |
| Customer value segments | 4 | observed-spend quartiles |

The segment label itself is **not** an input to renewal probability. Renewal is modeled from continuous observed features such as spend, repeat-order count, inferred cadence, and delivery delay; value quartiles are applied afterward for cohort comparison.

## Unit-test result

```text
5 passed
```

## Reproduce

```bash
make setup
make data       # or manually place Olist CSVs in data/raw/olist/
make run

# independent metric cross-check
PYTHONPATH=src .venv/bin/python scripts/crosscheck_metrics.py
```

Do not present modeled subscriber, churn, LTV, MRR-equivalent, or retention values as real Olist subscription behavior.
