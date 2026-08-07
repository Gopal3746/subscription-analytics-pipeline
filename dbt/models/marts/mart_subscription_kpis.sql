with by_sub as (
  select
    subscription_id,
    max(cycle_number) as cycles_observed,
    sum(billing_amount) as ltv,
    max(churned_this_cycle) as churned
  from {{ ref('stg_subscription_cycles') }}
  group by 1
)
select
  count(*) as synthetic_subscribers,
  sum(case when churned = 0 then 1 else 0 end) as active_subscriptions,
  round(avg(churned), 4) as churn_rate,
  round(avg(ltv), 2) as avg_ltv_brl,
  round(sum(ltv), 2) as synthetic_recurring_revenue_brl,
  round(avg(cycles_observed), 2) as avg_cycles_observed
from by_sub
