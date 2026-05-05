-- BOOK / Cahier de Recettes — Supabase schema
-- =============================================
-- Single canonical store for recipe edits. The public-facing site reads
-- recipes.json (regenerated when an admin clicks "Publier"); this DB holds
-- the live editable state, the audit trail, and the email whitelist.
--
-- Run this in Supabase Studio → SQL Editor as a single batch.
-- After this, run recipes_seed.sql to load the 598 existing recipes.

-- ============================================================
-- 1. RECIPES — full recipe JSON, one row per recipe
-- ============================================================
-- Storing as JSONB keeps the shape identical to recipes.json. Edits rewrite
-- the whole `data` field; that's fine at 598 rows.
create table if not exists public.recipes (
  id          integer primary key,                -- mirrors recipes.json id (gappy, not contiguous)
  data        jsonb   not null,                   -- full recipe: {title, numberLabel, ingredients[], steps[], notes, meta{}}
  updated_at  timestamptz not null default now(),
  updated_by  uuid    references auth.users(id) on delete set null
);
create index if not exists recipes_updated_at_idx on public.recipes (updated_at desc);

-- ============================================================
-- 2. EDIT_LOG — audit trail, one row per save
-- ============================================================
-- Stores the full before/after snapshot so we can roll back any single edit.
-- before_data is null for the initial seed (no prior state).
create table if not exists public.edit_log (
  id            bigint generated always as identity primary key,
  recipe_id     integer not null references public.recipes(id) on delete cascade,
  before_data   jsonb,
  after_data    jsonb   not null,
  edited_by     uuid    references auth.users(id) on delete set null,
  edited_by_email text,                            -- denormalized for quick display
  edited_at     timestamptz not null default now(),
  comment       text                               -- optional "what I fixed"
);
create index if not exists edit_log_recipe_idx on public.edit_log (recipe_id, edited_at desc);
create index if not exists edit_log_user_idx   on public.edit_log (edited_by, edited_at desc);

-- ============================================================
-- 3. ALLOWED_EMAILS — whitelist
-- ============================================================
-- Only emails listed here can sign in. Editing this table is admin-only
-- (RLS below). Seed with the initial editors.
create table if not exists public.allowed_emails (
  email      text primary key,
  added_at   timestamptz not null default now(),
  added_by   uuid references auth.users(id) on delete set null,
  is_admin   boolean not null default false      -- admins can manage the whitelist + publish
);

insert into public.allowed_emails (email, is_admin) values
  ('jeremyprince2903@gmail.com',      true),
  ('chantal.cadieux@mail.mcgill.ca',  false)
on conflict (email) do nothing;

-- ============================================================
-- 4. WHITELIST ENFORCEMENT
-- ============================================================
-- Reject auth.users insert if the email isn't in allowed_emails. This runs
-- before Supabase creates the user record, so non-whitelisted attempts get
-- a clean error instead of a stranded auth row.
create or replace function public.enforce_email_whitelist()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if not exists (select 1 from public.allowed_emails where lower(email) = lower(new.email)) then
    raise exception 'Email % is not authorized to sign in', new.email
      using errcode = '42501';   -- insufficient_privilege
  end if;
  return new;
end;
$$;

drop trigger if exists enforce_email_whitelist on auth.users;
create trigger enforce_email_whitelist
  before insert on auth.users
  for each row execute function public.enforce_email_whitelist();

-- ============================================================
-- 5. AUDIT TRIGGER — every recipes UPDATE writes to edit_log
-- ============================================================
create or replace function public.log_recipe_edit()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_email text;
begin
  -- Look up the editor's email for denormalized display
  select email into v_email from auth.users where id = new.updated_by;
  insert into public.edit_log (recipe_id, before_data, after_data, edited_by, edited_by_email)
    values (new.id, old.data, new.data, new.updated_by, v_email);
  return new;
end;
$$;

drop trigger if exists log_recipe_edit on public.recipes;
create trigger log_recipe_edit
  after update of data on public.recipes
  for each row
  when (old.data is distinct from new.data)
  execute function public.log_recipe_edit();

-- ============================================================
-- 6. ROW-LEVEL SECURITY
-- ============================================================
alter table public.recipes        enable row level security;
alter table public.edit_log       enable row level security;
alter table public.allowed_emails enable row level security;

-- recipes: any authenticated user (= whitelisted, since signup is gated) can read + update
drop policy if exists recipes_select_auth on public.recipes;
create policy recipes_select_auth on public.recipes
  for select to authenticated using (true);

drop policy if exists recipes_update_auth on public.recipes;
create policy recipes_update_auth on public.recipes
  for update to authenticated using (true) with check (true);

-- recipes: anon clients can also read (so the public site can fall back to DB
-- if recipes.json hasn't been republished yet — also useful for /edit preview)
drop policy if exists recipes_select_anon on public.recipes;
create policy recipes_select_anon on public.recipes
  for select to anon using (true);

-- edit_log: authenticated users can read history, only triggers can insert
drop policy if exists edit_log_select_auth on public.edit_log;
create policy edit_log_select_auth on public.edit_log
  for select to authenticated using (true);

-- allowed_emails: only admins (is_admin = true rows) can read or modify
drop policy if exists allowed_emails_admin on public.allowed_emails;
create policy allowed_emails_admin on public.allowed_emails
  for all to authenticated
  using (
    exists (
      select 1 from public.allowed_emails ae
      where lower(ae.email) = lower((auth.jwt() ->> 'email'))
        and ae.is_admin = true
    )
  )
  with check (
    exists (
      select 1 from public.allowed_emails ae
      where lower(ae.email) = lower((auth.jwt() ->> 'email'))
        and ae.is_admin = true
    )
  );

-- Also let any whitelisted user read their OWN whitelist row (so the UI can
-- check the is_admin flag for the logged-in user).
drop policy if exists allowed_emails_self_read on public.allowed_emails;
create policy allowed_emails_self_read on public.allowed_emails
  for select to authenticated
  using (lower(email) = lower((auth.jwt() ->> 'email')));

-- ============================================================
-- 7. HELPER VIEWS
-- ============================================================
-- Recent edits with editor email + recipe title — convenient for the dashboard
create or replace view public.v_recent_edits as
select
  el.id,
  el.recipe_id,
  el.edited_at,
  el.edited_by_email,
  el.comment,
  r.data ->> 'title'       as recipe_title,
  r.data ->> 'numberLabel' as recipe_label
from public.edit_log el
join public.recipes r on r.id = el.recipe_id
order by el.edited_at desc;

grant select on public.v_recent_edits to authenticated, anon;
