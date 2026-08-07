select subscription_id, cycle_number, count(*) as n
from {{ ref('stg_subscription_cycles') }}
group by 1,2
having count(*) > 1
