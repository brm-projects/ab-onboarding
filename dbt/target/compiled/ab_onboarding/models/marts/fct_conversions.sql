-- For onboarding: start vs complete (binary conversion per user)
with starts as (
  select distinct
    user_id, experiment_key
  from "abdb"."analytics_staging"."stg_events_raw"
  where event_type = 'signup_start'
),
completes as (
  select distinct
    user_id, experiment_key
  from "abdb"."analytics_staging"."stg_events_raw"
  where event_type = 'signup_complete'
),
kyc7 as (
  -- KYC completion within 7 days of start (guardrail)
  select
    e.user_id,
    e.experiment_key,
    min(e.ts) as kyc_ts
  from "abdb"."analytics_staging"."stg_events_raw" e
  where e.event_type = 'kyc_complete'
  group by 1,2
),
joined as (
  select
    exp.user_id,
    exp.experiment_key,
    exp.variant,
    exp.exposure_ts,
    case when s.user_id is not null then 1 else 0 end as started,
    case when c.user_id is not null then 1 else 0 end as completed,
    case
      when c.user_id is not null then 1
      else 0
    end as converted,
    case
      when k.kyc_ts is not null
           and k.kyc_ts <= exp.exposure_ts + interval '7 days'
      then 1 else 0
    end as kyc_7d
  from "abdb"."analytics_analytics"."fct_exposures" exp
  left join starts s
    on s.user_id = exp.user_id and s.experiment_key = exp.experiment_key
  left join completes c
    on c.user_id = exp.user_id and c.experiment_key = exp.experiment_key
  left join kyc7 k
    on k.user_id = exp.user_id and k.experiment_key = exp.experiment_key
)
select *
from joined