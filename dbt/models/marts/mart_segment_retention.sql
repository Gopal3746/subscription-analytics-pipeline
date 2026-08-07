with cohorts as (
  select value_segment, count(distinct subscription_id) as cohort_size
  from {{ ref('stg_subscription_cycles') }}
  where cycle_number = 1 and renewed = 1
  group by 1
)
select
  s.value_segment,
  s.cycle_number,
  c.cohort_size,
  count(distinct s.subscription_id) filter(where s.renewed = 1) as retained_subscribers,
  round(count(distinct s.subscription_id) filter(where s.renewed = 1)::double / c.cohort_size, 4) as retention_rate
from {{ ref('stg_subscription_cycles') }} s
join cohorts c using(value_segment)
group by 1,2,3
order by 1,2
