-- One row per user per experiment capturing first exposure and variant.
with base as (
  select
    user_id,
    experiment_key,
    variant,
    min(ts) as first_seen
  from "abdb"."analytics_staging"."stg_events_raw"
  group by 1,2,3
),
assign as (
  -- Prefer stored assignment if it exists to enforce stickiness
  select
    a.user_id,
    a.experiment_key,
    a.variant,
    a.assigned_at
  from "abdb"."analytics_staging"."stg_assignments" a
),
choose as (
  select
    coalesce(assign.user_id, base.user_id) as user_id,
    coalesce(assign.experiment_key, base.experiment_key) as experiment_key,
    coalesce(assign.variant, base.variant) as variant,
    coalesce(assign.assigned_at, base.first_seen) as exposure_ts
  from base
  full outer join assign
    on base.user_id = assign.user_id
   and base.experiment_key = assign.experiment_key
)
select *
from choose