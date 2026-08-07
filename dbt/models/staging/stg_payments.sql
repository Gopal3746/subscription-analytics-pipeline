select
  cast(order_id as varchar) as order_id,
  cast(payment_sequential as integer) as payment_sequential,
  cast(payment_type as varchar) as payment_type,
  cast(payment_installments as integer) as payment_installments,
  cast(payment_value as double) as payment_value
from {{ source('raw', 'payments') }}
