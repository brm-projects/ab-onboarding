create table if not exists experiments (
  id serial primary key,
  key text unique not null,
  name text not null,
  enabled boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists assignments (
  id bigserial primary key,
  user_id text not null,
  experiment_key text not null,
  variant text not null,
  assigned_at timestamptz not null default now(),
  unique (user_id, experiment_key)
);

create index if not exists idx_assignments_experiment_key on assignments (experiment_key);
create index if not exists idx_assignments_user on assignments (user_id);

create table if not exists events_raw (
  id bigserial primary key,
  ts timestamptz not null default now(),
  user_id text not null,
  experiment_key text not null,
  variant text not null,
  event_type text not null,
  metadata jsonb
);

create index if not exists idx_events_experiment_ts on events_raw (experiment_key, ts);
create index if not exists idx_events_user_ts on events_raw (user_id, ts);

insert into experiments (key, name, enabled)
values ('onboarding_progressive_v1', 'Progressive onboarding vs full KYC', true)
on conflict (key) do nothing;
