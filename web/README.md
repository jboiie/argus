# Argus dashboard (web)

Static React dashboard over the Supabase audit trail. Replaced the earlier
Streamlit app, now removed from the repo (see the root `README.md`'s
Dashboard section for screenshots). Not deployed — run it locally.

## Why a static SPA and not a backend

Every table has row-level security enabled with a **SELECT-only policy for
`anon`** (see `DataModel.md` → Security, and `scripts/setup_supabase.sql`).
That means the browser can query Supabase directly: there is nothing to
protect behind a server, because the key in the bundle cannot write.

`scripts/verify-rls.mjs` checks that property directly — it reads every table
with the anon key and then attempts one insert, which must fail:

```bash
node scripts/verify-rls.mjs
# runs: 37 rows ... write blocked by RLS: new row violates row-level security policy
```

Run it after any change to RLS policies. If the write ever succeeds, the anon
key is no longer safe to ship and this architecture is invalid.

**`SUPABASE_SERVICE_ROLE_KEY` must never appear in this directory.** Vite
inlines every `VITE_*` variable into the public bundle, and service_role
bypasses RLS entirely.

## Local

```bash
npm install
cp .env.example .env      # fill in VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY
npm run dev
```

## Build

```bash
npm run build             # -> dist/
npm run preview
```

## Rendering untrusted text

Attack prompts, agent responses, judge reasoning and session turns are
written by an adversarial generator or by a model answering one, and a
prompt-injection payload is routinely shaped to look like markup. They render
through the `Untrusted` component as literal monospace text. React escapes by
default and this app never uses `dangerouslySetInnerHTML` — keep it that way.
