
  
    

  create  table "abdb"."analytics"."agg_experiment_day__dbt_tmp"
  
  
    as
  
  (
    -- Daily metrics by experiment and variant
with events as (
  select
    date_trunc('day', exposure_ts) as day,
    experiment_key,
    variant,
    count(*) as users_exposed,
    sum(started) as started,
    sum(completed) as completed,
    avg(converted::float) as conversion_rate,
    avg(kyc_7d::float) as kyc_7d_rate
  from "abdb"."analytics"."fct_conversions"
  group by 1,2,3
)
select *
from events
order by day desc, experiment_key, variant
  );
  