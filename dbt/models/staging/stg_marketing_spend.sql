select
  cast(month as date) as month,
  cast(customer_state as varchar) as customer_state,
  cast(channel as varchar) as channel,
  cast(spend_brl as double) as spend_brl,
  cast(impressions as bigint) as impressions,
  cast(clicks as bigint) as clicks
from {{ source('raw', 'marketing_spend') }}
