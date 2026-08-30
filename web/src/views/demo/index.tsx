import { useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Activity, Compass, FastForward, ScrollText, ShieldAlert, Wallet, Zap } from "lucide-react";
import Dock from "../../components/Dock";
import { Overview, type CompletedActs } from "../Overview";
import { RedTeamAct, type RedTeamRow } from "./RedTeamAct";
import { DriftAct, type DriftUpdate } from "./DriftAct";
import { MandateAct, type MandateUpdate } from "./MandateAct";
import { DemoFindings } from "./DemoFindings";
import { setSpeed } from "../../lib/demoEngine";

/* A traversable mini-dashboard, not one linear scripted page: the same four
 * sections as the real dashboard (Overview / Red Team / Drift / Mandates),
 * navigable directly via its own Dock rather than forcing a sit-through of
 * every act in order. Each act owns its own Run/Pause/Replay - jumping
 * straight to Drift or Mandates for the video doesn't require Red Team to
 * have played first. */

const DEMO_NAV = [
  { id: "overview", label: "Overview", icon: Compass },
  { id: "findings", label: "Findings", icon: ShieldAlert },
  { id: "redteam", label: "Red Team", icon: ScrollText },
  { id: "drift", label: "Drift", icon: Activity },
  { id: "mandates", label: "Mandates", icon: Wallet },
] as const;
type DemoTab = (typeof DEMO_NAV)[number]["id"];

const SPEEDS = [1, 2, 4] as const;

/* One-button auto-pilot for the video: plays one representative attack from
 * each act in sequence, landing on the live Findings rollup at the end. Each
 * step names the tab to switch to and the scenario key to auto-play there;
 * the receiving act auto-plays it on mount via its `autoPlay` prop. */
const AUTO_SEQUENCE: { tab: DemoTab; key?: string }[] = [
  { tab: "redteam", key: "confirmation_forgery" },
  { tab: "drift", key: "stale" },
  { tab: "mandates", key: "quoted_system_confirmation" },
  { tab: "findings" },
];

export function Demo({ onExit }: { onExit: () => void }) {
  const [tab, setTab] = useState<DemoTab>("overview");
  const [completed, setCompleted] = useState<CompletedActs>({
    redteam: false,
    drift: false,
    mandates: false,
  });
  const [speedIdx, setSpeedIdx] = useState(0);
  const [autoStep, setAutoStep] = useState<number | null>(null);
  const autoNonce = useRef(0);

  // Lifted here (not owned by the acts) so Findings stays current even after
  // an act unmounts on tab switch and its own local state resets.
  const [redteamFindings, setRedteamFindings] = useState<RedTeamRow[]>([]);
  const [driftFindings, setDriftFindings] = useState<DriftUpdate | null>(null);
  const [mandateFindings, setMandateFindings] = useState<MandateUpdate | null>(null);

  function changeSpeed() {
    const next = (speedIdx + 1) % SPEEDS.length;
    setSpeedIdx(next);
    setSpeed(SPEEDS[next]);
  }

  function runEverything() {
    autoNonce.current += 1;
    setAutoStep(0);
    setTab(AUTO_SEQUENCE[0].tab);
  }

  function advanceAuto() {
    setAutoStep((step) => {
      if (step === null) return null;
      const next = step + 1;
      if (next >= AUTO_SEQUENCE.length) return null;
      autoNonce.current += 1;
      setTab(AUTO_SEQUENCE[next].tab);
      return next;
    });
  }

  const autoKey = autoStep !== null ? AUTO_SEQUENCE[autoStep].key : undefined;

  return (
    <div className="pb-32">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-3 border border-caution/50 bg-chrome px-5 py-3">
        <div className="flex items-center gap-2.5">
          <span className="h-2 w-2 animate-pulse rounded-full bg-caution" />
          <span className="font-mono text-2xs font-semibold tracking-[0.16em] text-caution uppercase">
            Simulated — for presentation only, no live data or API calls
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={changeSpeed}
            title="Playback speed"
            className="inline-flex items-center gap-1.5 rounded-md border border-ink-3 bg-chrome-2 px-3 py-1.5 font-mono text-2xs font-bold tracking-[0.14em] text-ink-2 uppercase transition-colors hover:border-brass hover:text-brass"
          >
            <FastForward className="size-3.5" strokeWidth={2} aria-hidden="true" />
            {SPEEDS[speedIdx]}x
          </button>
          <button
            onClick={runEverything}
            title="Auto-play one scenario from each act"
            className="inline-flex items-center gap-1.5 rounded-md border border-brass bg-brass/10 px-3 py-1.5 font-mono text-2xs font-bold tracking-[0.14em] text-brass uppercase shadow-[0_0_14px_-4px_rgba(201,162,39,0.7)] transition-colors hover:bg-brass hover:text-void"
          >
            <Zap className="size-3.5" strokeWidth={2} aria-hidden="true" />
            Run everything
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.28, ease: [0.2, 0.7, 0.3, 1] }}
        >
          {tab === "overview" ? <Overview completedActs={completed} /> : null}
          {tab === "findings" ? (
            <DemoFindings redteam={redteamFindings} drift={driftFindings} mandate={mandateFindings} />
          ) : null}
          {tab === "redteam" ? (
            <RedTeamAct
              onExit={onExit}
              onComplete={() => {
                setCompleted((c) => ({ ...c, redteam: true }));
                if (autoStep !== null && AUTO_SEQUENCE[autoStep].tab === "redteam") advanceAuto();
              }}
              onUpdate={setRedteamFindings}
              autoPlay={autoStep !== null && AUTO_SEQUENCE[autoStep].tab === "redteam" ? autoKey : undefined}
              autoNonce={autoNonce.current}
            />
          ) : null}
          {tab === "drift" ? (
            <DriftAct
              onExit={onExit}
              onComplete={() => {
                setCompleted((c) => ({ ...c, drift: true }));
                if (autoStep !== null && AUTO_SEQUENCE[autoStep].tab === "drift") advanceAuto();
              }}
              onUpdate={setDriftFindings}
              autoPlay={autoStep !== null && AUTO_SEQUENCE[autoStep].tab === "drift" ? autoKey : undefined}
              autoNonce={autoNonce.current}
            />
          ) : null}
          {tab === "mandates" ? (
            <MandateAct
              onExit={onExit}
              onComplete={() => {
                setCompleted((c) => ({ ...c, mandates: true }));
                if (autoStep !== null && AUTO_SEQUENCE[autoStep].tab === "mandates") advanceAuto();
              }}
              onUpdate={setMandateFindings}
              autoPlay={autoStep !== null && AUTO_SEQUENCE[autoStep].tab === "mandates" ? autoKey : undefined}
              autoNonce={autoNonce.current}
            />
          ) : null}
        </motion.div>
      </AnimatePresence>

      <Dock
        items={DEMO_NAV.map((n) => {
          const Icon = n.icon;
          const done = n.id === "redteam" ? completed.redteam : n.id === "drift" ? completed.drift : n.id === "mandates" ? completed.mandates : false;
          return {
            label: n.label,
            active: tab === n.id,
            onClick: () => setTab(n.id),
            icon: (
              <span className="relative inline-flex">
                <Icon className="size-[18px]" strokeWidth={2} aria-hidden="true" />
                {done ? (
                  <span
                    className="absolute -top-0.5 -right-0.5 h-1.5 w-1.5 rounded-full bg-verdict"
                    aria-hidden="true"
                  />
                ) : null}
              </span>
            ),
          };
        })}
      />
    </div>
  );
}
