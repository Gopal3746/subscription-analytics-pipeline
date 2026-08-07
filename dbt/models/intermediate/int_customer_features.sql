select
  customer_unique_id,
  any_value(customer_state) as customer_state,
  min(order_purchase_timestamp)::date as first_order_date,
  count(distinct order_id) as order_count,
  sum(payment_value) as observed_revenue,
  avg(payment_value) as avg_order_value
from {{ ref('int_order_facts') }}
where order_status = 'delivered'
group by 1
