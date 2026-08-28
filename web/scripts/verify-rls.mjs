// Confirms the browser-side access pattern works: anon key, RLS SELECT-only,
// no backend. Same queries the app issues.
import { createClient } from "@supabase/supabase-js";
import fs from "node:fs";
const env = Object.fromEntries(
  fs.readFileSync(".env", "utf8").split("\n").filter(Boolean).map((l) => l.split("=").map((s) => s.trim())),
);
const sb = createClient(env.VITE_SUPABASE_URL, env.VITE_SUPABASE_ANON_KEY);
for (const [table, order] of [["runs", "started_at"], ["attack_events", "timestamp"], ["drift_incidents", "timestamp"], ["mandates", "authorized_at"]]) {
  const { data, error } = await sb.from(table).select("*").order(order, { ascending: false }).limit(5000);
  console.log(error ? `${table}: ERROR ${error.message}` : `${table}: ${data.length} rows`);
}
// RLS must refuse a write from the anon key.
const { error: wErr } = await sb.from("runs").insert({ run_type: "redteam", label: "rls_probe" });
console.log(wErr ? `write blocked by RLS: ${wErr.message.slice(0, 70)}` : "!! WRITE SUCCEEDED - RLS IS NOT PROTECTING THIS TABLE");
