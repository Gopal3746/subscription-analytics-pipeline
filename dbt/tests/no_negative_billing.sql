select * from {{ ref('stg_subscription_cycles') }} where billing_amount < 0
