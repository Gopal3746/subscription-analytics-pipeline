select
  subscription_id,
  customer_unique_id,
  any_value(value_segment) as value_segment,
  sum(billing_amount) as synthetic_ltv_brl,
  sum(renewed) as active_cycles,
  max(churned_this_cycle) as churned
from {{ ref('stg_subscription_cycles') }}
group by 1,2
