# Cahier de Recettes — Editor backend setup

Step-by-step guide to provision the Supabase project the editor talks to.
This is a one-time setup. After it, all editor work is in the app itself.

You'll need ~15 minutes and a credit card-free Supabase account (the free
tier is plenty: 500 MB database, 50 000 monthly active users).

## 1. Create a Supabase account + project

1. Go to <https://supabase.com> → **Start your project**.
2. Sign up with GitHub or email.
3. Click **New project** in the dashboard.
   - **Name**: `cahier-de-recettes`
   - **Database password**: generate a strong one and save it in your password
     manager. You won't need it day-to-day, but you can't recover it later.
   - **Region**: pick the one closest to Quebec (e.g. *East US (North Virginia)*).
   - **Pricing plan**: **Free**.
4. Wait ~1 minute for provisioning.

## 2. Run the schema

1. Once the project is up, click **SQL Editor** in the left sidebar.
2. Click **+ New query**.
3. Open `db/schema.sql` from this repo (in your editor or VS Code).
4. Copy the entire contents → paste into the Supabase SQL editor.
5. Click **Run** (or `Ctrl+Enter`). You should see *Success. No rows returned.*

## 3. Seed the existing 598 recipes

1. Still in the SQL Editor, click **+ New query**.
2. Open `db/recipes_seed.sql` (auto-generated, 575 KB — this is normal).
3. Copy → paste → **Run**. It takes ~5 seconds.
4. Verify: in the left sidebar click **Table Editor** → **recipes**. You should see 598 rows.

> If you ever change `recipes.json` outside the editor (e.g., manual edits),
> regenerate the seed file with `python tools/generate_recipes_seed.py` and
> re-run it. The script uses `ON CONFLICT DO UPDATE`, so it's safe to re-run.

## 4. Configure email auth

1. Sidebar → **Authentication** → **Providers**.
2. **Email** is enabled by default. Confirm:
   - *Enable Email provider* — **on**
   - *Confirm email* — **on**  (magic-link flow needs this)
   - *Secure email change* — **on**
3. (Optional but nice) Sidebar → **Authentication** → **Email Templates** →
   **Magic Link**. Customize the French copy. Suggested:
   - **Subject**: `Connexion au Cahier de Recettes`
   - **Body**: replace the placeholder text with something warmer (the link
     placeholder is `{{ .ConfirmationURL }}` — keep that).

## 5. Copy the project URL + anon key into the app

1. Sidebar → **Settings** → **API**.
2. Copy two values:
   - **Project URL** (something like `https://xxxxxxxxxxxxx.supabase.co`)
   - **Project API keys → `anon` `public`** (a long JWT-looking string)
3. Open `assets/auth-config.js` in this repo and replace the placeholders:
   ```js
   export const SUPABASE_URL      = "https://xxxxxxxxxxxxx.supabase.co";
   export const SUPABASE_ANON_KEY = "eyJhbGc...";
   ```
4. Commit + push. Vercel redeploys. Login is live.

> The `anon` key is **safe to commit** — it's designed for client-side use and
> security comes from Row-Level Security policies, not from the key being
> secret. Never commit the **service_role** key, which bypasses RLS.

## 6. Add new editors (later)

To grant edit access to another family member:
1. SQL Editor → run:
   ```sql
   insert into public.allowed_emails (email, is_admin)
     values ('cousin@example.com', false);
   ```
2. Tell them to go to your site → **Connexion** → enter that exact email →
   click the magic link in their email. They're in.

## Troubleshooting

| Problem | Fix |
|---|---|
| Login form says "Email not authorized" | The email isn't in `allowed_emails`. Add it (step 6). |
| Magic link emails not arriving | Check spam. Supabase free tier sends from `noreply@mail.app.supabase.io` — the user's mail provider may be filtering. You can configure custom SMTP under Authentication → Settings if it becomes a problem. |
| "Permission denied for table recipes" | RLS is working as intended. Confirm the user's email is in `allowed_emails`. |
| Need to roll back a bad edit | SQL Editor → look up the offending row in `edit_log` → `update recipes set data = (select before_data from edit_log where id = ?) where id = ?`. |
