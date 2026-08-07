select
  cast(product_id as varchar) as product_id,
  cast(product_category_name as varchar) as product_category_name,
  cast(product_name_lenght as integer) as product_name_length,
  cast(product_description_lenght as integer) as product_description_length,
  cast(product_photos_qty as integer) as product_photos_qty,
  cast(product_weight_g as double) as product_weight_g
from {{ source('raw', 'products') }}
