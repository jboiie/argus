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
import Dock from "./components/Dock";
import Shuffle from "./components/Shuffle";
import { Spotlight } from "./components/Spotlight";

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
    <div className="relative min-h-full">
      <div className="atmosphere" aria-hidden="true" />
      <Spotlight />

      {/* Chrome floats now. A thin mark rather than a header bar — the rail was
          a permanent 224px of furniture competing with the record. */}
      <div className="relative z-10 flex items-center justify-between px-6 pt-5 sm:px-10">
        <div className="flex items-center gap-2.5">
          <Eye className="size-4 text-brass" strokeWidth={2} aria-hidden="true" />
          <Shuffle
            text="ARGUS"
            tag="span"
            textAlign="left"
            className="font-mono text-[17px] font-semibold tracking-[0.24em] text-ink"
            shuffleDirection="down"
            duration={0.3}
            shuffleTimes={2}
            stagger={0.035}
            scrambleCharset="ARGUS01<>#/\\"
            colorFrom="var(--color-brass)"
            colorTo="var(--color-ink)"
            triggerOnHover
          />
          <span className="hidden h-3 w-px bg-rule sm:block" />
          <span className="hidden font-mono text-2xs tracking-[0.18em] text-ink-3 uppercase sm:block">
            {active.blurb}
          </span>
        </div>
        <a
          className="font-mono text-2xs tracking-[0.14em] text-ink-3 uppercase transition-colors hover:text-brass"
          href="https://github.com/jboiie/argus"
        >
          github.com/jboiie/argus
        </a>
      </div>

      {/* pb-40 clears the dock so no content is ever trapped behind it. */}
      <main className="relative z-10 px-6 pt-8 pb-40 sm:px-10">
        {!isConfigured ? (
          <Note tone="warn">
            <code>VITE_SUPABASE_URL</code> / <code>VITE_SUPABASE_ANON_KEY</code> are not configured.
            Copy <code>.env.example</code> to <code>.env</code> and fill them in.
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

        <p className="mx-auto mt-24 max-w-2xl text-center font-mono text-2xs leading-relaxed text-ink-3">
          Read-only · anon key is SELECT-only behind row-level security · the service-role key never
          reaches this app
        </p>
      </main>

      <Dock
        items={NAV.map((n) => {
          const Icon = n.icon;
          return {
            label: n.label,
            active: tab === n.id,
            onClick: () => setTab(n.id),
            icon: <Icon className="size-[18px]" strokeWidth={2} aria-hidden="true" />,
          };
        })}
      />
    </div>
  );
}
