with base as (
  select
    subscription_id,
    date_trunc('month', min(billing_date) over(partition by subscription_id))::date as cohort_month,
    cycle_number,
    renewed
  from {{ ref('stg_subscription_cycles') }}
), cohorts as (
  select cohort_month, count(distinct subscription_id) as cohort_size
  from base where cycle_number = 1 and renewed = 1 group by 1
)
select
  b.cohort_month,
  b.cycle_number,
  c.cohort_size,
  count(distinct b.subscription_id) filter(where b.renewed = 1) as retained_subscribers,
  round(count(distinct b.subscription_id) filter(where b.renewed = 1)::double / c.cohort_size, 4) as retention_rate
from base b
join cohorts c using(cohort_month)
group by 1,2,3
order by 1,2
