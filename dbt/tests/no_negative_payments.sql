select * from {{ ref('stg_payments') }} where payment_value < 0
