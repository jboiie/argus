import { useEffect, useState } from "react";
import { fetchAttackEvents, fetchDriftIncidents, fetchMandates, fetchRuns } from "./lib/data";
import { isConfigured } from "./lib/supabase";
import type { AttackEvent, DriftIncident, Mandate, Run } from "./lib/types";
import { Findings } from "./views/Findings";
import { RedTeam } from "./views/RedTeam";
import { Drift } from "./views/Drift";
import { Mandates as MandatesView } from "./views/Mandates";
import { Note, Panel } from "./components/ui";

const TABS = ["Findings", "Pre-Deployment · Red Team", "Post-Deployment · Drift", "Mandates"] as const;
type Tab = (typeof TABS)[number];

export default function App() {
  const [tab, setTab] = useState<Tab>("Findings");
  const [events, setEvents] = useState<AttackEvent[]>([]);
  const [incidents, setIncidents] = useState<DriftIncident[]>([]);
  const [mandates, setMandates] = useState<Mandate[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isConfigured) {
      setLoading(false);
      return;
    }
    Promise.all([fetchAttackEvents(), fetchDriftIncidents(), fetchMandates(), fetchRuns()])
      .then(([e, i, m, r]) => {
        setEvents(e);
        setIncidents(i);
        setMandates(m);
        setRuns(r);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="mx-auto min-h-full max-w-7xl px-5 py-8">
      <header className="mb-7">
        <div className="flex items-baseline gap-3">
          <span className="text-3xl">👁</span>
          <h1 className="text-3xl font-bold tracking-tight text-ink">Argus</h1>
        </div>
        <p className="mt-1 text-base font-medium text-accent-dim">
          Agent QA &amp; Monitoring for Agentic Commerce
        </p>
        <p className="mt-2 max-w-4xl text-sm leading-relaxed text-ink-dim">
          A pre-deployment red-team harness and a post-deployment drift sentinel, both run against
          one reference commerce agent. Read-only view over the full audit trail: every attack
          attempt, every ground-truth check, and every money-moving authorization.
        </p>
      </header>

      <nav className="mb-6 flex flex-wrap gap-1 border-b border-edge">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`-mb-px border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === t
                ? "border-accent text-accent"
                : "border-transparent text-ink-dim hover:text-ink"
            }`}
          >
            {t}
          </button>
        ))}
      </nav>

      {!isConfigured ? (
        <Note tone="warn">
          <code>VITE_SUPABASE_URL</code> / <code>VITE_SUPABASE_ANON_KEY</code> are not configured.
          Copy <code>.env.example</code> to <code>.env</code> and fill them in.
        </Note>
      ) : error ? (
        <Note tone="bad">Couldn't reach Supabase: {error}</Note>
      ) : loading ? (
        <Panel>
          <p className="text-sm text-ink-dim">Loading…</p>
        </Panel>
      ) : (
        <main>
          {tab === "Findings" ? <Findings incidents={incidents} /> : null}
          {tab === "Pre-Deployment · Red Team" ? <RedTeam events={events} runs={runs} /> : null}
          {tab === "Post-Deployment · Drift" ? <Drift incidents={incidents} runs={runs} /> : null}
          {tab === "Mandates" ? <MandatesView mandates={mandates} /> : null}
        </main>
      )}

      <footer className="mt-10 border-t border-edge pt-5 text-xs text-ink-dim">
        Razorpay AI Builder Buildathon · Open Track ·{" "}
        <a className="text-accent-dim hover:underline" href="https://github.com/jboiie/argus">
          github.com/jboiie/argus
        </a>
        <span className="mx-2">·</span>
        Read-only. The anon key is SELECT-only behind row-level security; the service-role key never
        reaches this app.
      </footer>
    </div>
  );
}
