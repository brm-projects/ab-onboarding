
  create view "abdb"."analytics_staging"."stg_events_raw__dbt_tmp"
    
    
  as (
    with src as (
  select
    id,
    ts,
    user_id,
    experiment_key,
    variant,
    event_type,
    metadata
  from "abdb"."public"."events_raw"
)
select
  id,
  ts,
  user_id,
  lower(experiment_key) as experiment_key,
  upper(variant) as variant,
  lower(event_type) as event_type,
  metadata
from src
  );