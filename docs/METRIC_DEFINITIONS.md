# Metric definitions

## Observed commerce metrics

- **Real orders:** row count of `raw.orders`, sourced from `olist_orders_dataset.csv` after Spark deduplication.
- **Observed revenue:** sum of Olist `payment_value` after aggregating payments to order grain.
- **Observed customer:** Olist `customer_unique_id`, used to connect identities across order-specific customer IDs.

## Synthetic subscription metrics

These metrics are model-derived and must be labeled synthetic in documentation and interviews.

- **Synthetic subscriber:** an observed Olist customer deterministically selected into the modeled recurring program.
- **MRR-equivalent:** generated recurring-cycle billing amount based on observed average order value; not audited subscription revenue.
- **Churn:** modeled subscriber active in a prior cycle who does not renew the next generated cycle.
- **LTV:** cumulative synthetic billing amount across active modeled cycles.
- **Cycle-N retention:** subscribers active in modeled cycle N divided by cycle-1 subscribers.
- **Retention variance:** maximum minus minimum cycle-3 retention among eligible customer value segments, in percentage points.
