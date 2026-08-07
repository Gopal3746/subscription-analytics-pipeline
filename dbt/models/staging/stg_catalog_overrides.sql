select
  cast(product_id as varchar) as product_id,
  cast(catalog_tier as varchar) as catalog_tier,
  cast(subscription_eligible as integer) as subscription_eligible,
  cast(margin_band as varchar) as margin_band
from {{ source('raw', 'catalog_overrides') }}
