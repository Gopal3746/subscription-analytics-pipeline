select
  cast(subscription_id as varchar) as subscription_id,
  cast(customer_unique_id as varchar) as customer_unique_id,
  cast(cycle_number as integer) as cycle_number,
  cast(billing_date as date) as billing_date,
  cast(billing_amount as double) as billing_amount,
  cast(renewed as integer) as renewed,
  cast(churned_this_cycle as integer) as churned_this_cycle,
  cast(customer_state as varchar) as customer_state,
  cast(value_segment as varchar) as value_segment,
  cast(cadence_days as integer) as cadence_days
from {{ source('raw', 'synthetic_subscription_cycles') }}
