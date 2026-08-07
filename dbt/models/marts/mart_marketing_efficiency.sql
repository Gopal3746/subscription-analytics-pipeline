with revenue as (
  select
    order_month as month,
    customer_state,
    sum(payment_value) as observed_revenue_brl,
    count(distinct order_id) as orders
  from {{ ref('int_order_facts') }}
  where order_status = 'delivered'
  group by 1,2
), spend as (
  select month, customer_state, sum(spend_brl) as marketing_spend_brl
  from {{ ref('stg_marketing_spend') }}
  group by 1,2
)
select
  coalesce(r.month, s.month) as month,
  coalesce(r.customer_state, s.customer_state) as customer_state,
  coalesce(r.orders, 0) as orders,
  round(coalesce(r.observed_revenue_brl, 0), 2) as observed_revenue_brl,
  round(coalesce(s.marketing_spend_brl, 0), 2) as marketing_spend_brl,
  round(coalesce(r.observed_revenue_brl, 0) / nullif(s.marketing_spend_brl, 0), 3) as modeled_roas
from revenue r
full outer join spend s using(month, customer_state)
