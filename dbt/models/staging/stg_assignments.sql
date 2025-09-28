with src as (
  select
    user_id,
    experiment_key,
    variant,
    assigned_at
  from {{ source('raw', 'assignments') }}
)
select
  user_id,
  lower(experiment_key) as experiment_key,
  upper(variant) as variant,
  assigned_at
from src
