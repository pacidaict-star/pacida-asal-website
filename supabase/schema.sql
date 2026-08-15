-- PACIDA staff admin panel — Postgres schema (run once in the Supabase SQL editor)
--
-- Design notes (see C:\Users\l.muchemi\.claude\plans\stateless-snuggling-flask.md for full context):
--   - Status is never stored. "ongoing" vs "completed" is always derived from end_date by the
--     projects_live view below, re-evaluated on every query — no cron, no generated column
--     (Postgres rejects CURRENT_DATE in GENERATED ALWAYS AS; it isn't IMMUTABLE).
--   - project_locations is a separate one-to-many table because a handful of real PACIDA
--     projects legitimately span two counties.
--   - RLS is the actual security boundary here, not the anon key (which is meant to be public).
--     This schema is useless as a security control unless self-signup is ALSO disabled in
--     Authentication -> Providers -> Email in the Supabase dashboard — do that too.

create extension if not exists "pgcrypto"; -- gen_random_uuid()

create table public.projects (
  id              uuid primary key default gen_random_uuid(),
  title           text not null,
  donor           text,
  theme           text not null check (theme in (
                    'Climate Change','Disaster Risk Reduction','Education','Emergency',
                    'Health & Nutrition','Livelihood','Other','Peace & Governance','WASH')),
  start_date      date not null,
  end_date        date,                          -- null = open-ended, never auto-closes
  population_note text,
  created_by      uuid references auth.users(id),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  constraint end_after_start check (end_date is null or end_date >= start_date)
);

create table public.project_locations (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid not null references public.projects(id) on delete cascade,
  slug        text not null check (slug in ('marsabit','samburu','isiolo','borena')),
  kind        text not null check (kind in ('site','regional','county')),
  name        text not null,
  lat         double precision not null,
  lon         double precision not null
);
create index project_locations_project_id_idx on public.project_locations(project_id);
create index project_locations_slug_idx on public.project_locations(slug);

-- keep updated_at current on every edit
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger trg_projects_updated_at
  before update on public.projects
  for each row execute function public.set_updated_at();

-- derived status — this IS the "auto close when time is done" behaviour. No staff action,
-- no scheduled job: every read of this view recomputes status from today's date.
create view public.projects_live
with (security_invoker = true) as
select
  p.*,
  case
    when p.end_date is null or p.end_date >= current_date then 'ongoing'
    else 'completed'
  end as status
from public.projects p;

grant select on public.projects_live to anon, authenticated;

-- Row Level Security: anon (public map visitors) read-only; authenticated (invited PACIDA
-- staff — self-signup must be disabled in the dashboard, see note at top) full CRUD.
alter table public.projects enable row level security;
alter table public.project_locations enable row level security;

create policy anon_select_projects on public.projects
  for select to anon using (true);
create policy anon_select_locations on public.project_locations
  for select to anon using (true);

create policy staff_all_projects on public.projects
  for all to authenticated using (true) with check (true);
create policy staff_all_locations on public.project_locations
  for all to authenticated using (true) with check (true);
