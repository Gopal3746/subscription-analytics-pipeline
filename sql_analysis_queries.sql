-- KPI snapshot
select *
from analytics.mart_subscription_kpis;

-- Segment retention curve
select value_segment, cycle_number, cohort_size, retained_subscribers, retention_rate
from analytics.mart_segment_retention
order by value_segment, cycle_number;

-- Cohort retention curve
select cohort_month, cycle_number, cohort_size, retained_subscribers, retention_rate
from analytics.mart_cohort_retention
order by cohort_month, cycle_number;

-- Highest vs. lowest cycle-3 segment retention
with cycle3 as (
    select value_segment, retention_rate
    from analytics.mart_segment_retention
    where cycle_number = 3
)
select
    max(retention_rate) as highest_retention,
    min(retention_rate) as lowest_retention,
    (max(retention_rate) - min(retention_rate)) * 100 as spread_percentage_points
from cycle3;
