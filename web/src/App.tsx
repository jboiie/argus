import { useEffect, useState } from "react";
import { Activity, Eye, ScrollText, ShieldAlert, Wallet } from "lucide-react";
import { fetchAttackEvents, fetchDriftIncidents, fetchMandates, fetchRuns } from "./lib/data";
import { isConfigured } from "./lib/supabase";
import type { AttackEvent, DriftIncident, Mandate, Run } from "./lib/types";
import { Findings } from "./views/Findings";
import { RedTeam } from "./views/RedTeam";
import { Drift } from "./views/Drift";
import { Mandates as MandatesView } from "./views/Mandates";
import { LoadingView, Note } from "./components/ui";

const NAV = [
  { id: "findings", label: "Findings", icon: ShieldAlert, blurb: "What the harness caught" },
  { id: "redteam", label: "Red Team", icon: ScrollText, blurb: "Pre-deployment attack results" },
  { id: "drift", label: "Drift", icon: Activity, blurb: "Post-deployment ground-truth checks" },
  { id: "mandates", label: "Mandates", icon: Wallet, blurb: "Money-action authorization trail" },
] as const;
type TabId = (typeof NAV)[number]["id"];

export default function App() {
  const [tab, setTab] = useState<TabId>("findings");
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

  const active = NAV.find((n) => n.id === tab)!;

  return (
    <div className="flex min-h-full flex-col lg:flex-row">
      {/* Rail. Horizontal on small screens, fixed column from lg up. */}
      <aside className="shrink-0 border-b border-rule bg-chrome lg:sticky lg:top-0 lg:h-screen lg:w-56 lg:overflow-y-auto lg:border-r lg:border-b-0">
        <div className="flex items-center gap-2 px-4 py-4">
          <Eye className="size-5 text-brass" strokeWidth={2} aria-hidden="true" />
          <div>
            <div className="text-[15px] leading-none font-bold tracking-tight text-ink">Argus</div>
            <div className="mt-1 font-mono text-2xs tracking-[0.16em] text-ink-3 uppercase">
              Agent QA &amp; Monitoring
            </div>
          </div>
        </div>

        <nav
          aria-label="Sections"
          className="flex gap-1 overflow-x-auto px-2 pb-2 lg:flex-col lg:overflow-visible lg:pb-4"
          onKeyDown={(e) => {
            const i = NAV.findIndex((n) => n.id === tab);
            if (e.key === "ArrowDown" || e.key === "ArrowRight")
              setTab(NAV[(i + 1) % NAV.length].id);
            if (e.key === "ArrowUp" || e.key === "ArrowLeft")
              setTab(NAV[(i - 1 + NAV.length) % NAV.length].id);
          }}
        >
          {NAV.map((n) => {
            const Icon = n.icon;
            const on = tab === n.id;
            return (
              <button
                key={n.id}
                onClick={() => setTab(n.id)}
                aria-current={on ? "page" : undefined}
                tabIndex={on ? 0 : -1}
                className={`flex shrink-0 cursor-pointer items-center gap-2.5 px-2.5 py-2 text-left text-[13px] font-medium whitespace-nowrap transition-colors duration-150 lg:w-full ${
                  on
                    ? "bg-brass/10 text-brass shadow-[inset_2px_0_0_0_var(--color-brass)]"
                    : "text-ink-2 hover:bg-chrome-2 hover:text-ink"
                }`}
              >
                <Icon className="size-4 shrink-0" strokeWidth={2} aria-hidden="true" />
                {n.label}
              </button>
            );
          })}
        </nav>

        <div className="hidden border-t border-rule px-4 py-3 text-2xs leading-relaxed text-ink-3 lg:block">
          <p>Razorpay AI Builder Buildathon · Open Track</p>
          <a
            className="mt-1 inline-block text-brass hover:underline"
            href="https://github.com/jboiie/argus"
          >
            github.com/jboiie/argus
          </a>
          <p className="mt-2">
            Read-only. The anon key is SELECT-only behind row-level security; the service-role key
            never reaches this app.
          </p>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="border-b border-rule px-5 py-3.5">
          <h1 className="text-lg leading-tight font-semibold text-ink">{active.label}</h1>
          <p className="mt-0.5 text-xs text-ink-3">{active.blurb}</p>
        </header>

        <main className="space-y-4 p-5">
          {!isConfigured ? (
            <Note tone="warn">
              <code>VITE_SUPABASE_URL</code> / <code>VITE_SUPABASE_ANON_KEY</code> are not
              configured. Copy <code>.env.example</code> to <code>.env</code> and fill them in.
            </Note>
          ) : error ? (
            <Note tone="bad">Couldn't reach Supabase: {error}</Note>
          ) : loading ? (
            <LoadingView />
          ) : (
            <>
              {tab === "findings" ? <Findings incidents={incidents} /> : null}
              {tab === "redteam" ? <RedTeam events={events} runs={runs} /> : null}
              {tab === "drift" ? <Drift incidents={incidents} runs={runs} /> : null}
              {tab === "mandates" ? <MandatesView mandates={mandates} /> : null}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
