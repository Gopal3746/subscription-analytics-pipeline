with payments as (
  select order_id, sum(payment_value) as payment_value
  from {{ ref('stg_payments') }} group by 1
), items as (
  select order_id,
         count(*) as item_count,
         sum(price) as item_revenue,
         sum(freight_value) as freight_value
  from {{ ref('stg_order_items') }} group by 1
)
select
  o.order_id,
  c.customer_unique_id,
  c.customer_state,
  o.order_status,
  o.order_purchase_timestamp,
  date_trunc('month', o.order_purchase_timestamp)::date as order_month,
  coalesce(p.payment_value, 0) as payment_value,
  coalesce(i.item_count, 0) as item_count,
  coalesce(i.item_revenue, 0) as item_revenue,
  coalesce(i.freight_value, 0) as freight_value
from {{ ref('stg_orders') }} o
join {{ ref('stg_customers') }} c using(customer_id)
left join payments p using(order_id)
left join items i using(order_id)
