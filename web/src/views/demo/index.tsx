import { useState } from "react";
import { Activity, Compass, ScrollText, Wallet } from "lucide-react";
import Dock from "../../components/Dock";
import { Overview, type CompletedActs } from "../Overview";
import { RedTeamAct } from "./RedTeamAct";
import { DriftAct } from "./DriftAct";
import { MandateAct } from "./MandateAct";

/* A traversable mini-dashboard, not one linear scripted page: the same four
 * sections as the real dashboard (Overview / Red Team / Drift / Mandates),
 * navigable directly via its own Dock rather than forcing a sit-through of
 * every act in order. Each act owns its own Run/Pause/Replay - jumping
 * straight to Drift or Mandates for the video doesn't require Red Team to
 * have played first. */

const DEMO_NAV = [
  { id: "overview", label: "Overview", icon: Compass },
  { id: "redteam", label: "Red Team", icon: ScrollText },
  { id: "drift", label: "Drift", icon: Activity },
  { id: "mandates", label: "Mandates", icon: Wallet },
] as const;
type DemoTab = (typeof DEMO_NAV)[number]["id"];

export function Demo({ onExit }: { onExit: () => void }) {
  const [tab, setTab] = useState<DemoTab>("overview");
  const [completed, setCompleted] = useState<CompletedActs>({
    redteam: false,
    drift: false,
    mandates: false,
  });

  return (
    <div className="pb-32">
      <div className="mb-8 flex items-center gap-2.5 border border-caution/50 bg-chrome px-5 py-3">
        <span className="h-2 w-2 animate-pulse rounded-full bg-caution" />
        <span className="font-mono text-2xs font-semibold tracking-[0.16em] text-caution uppercase">
          Simulated — for presentation only, no live data or API calls
        </span>
      </div>

      {tab === "overview" ? <Overview completedActs={completed} /> : null}
      {tab === "redteam" ? (
        <RedTeamAct onComplete={() => setCompleted((c) => ({ ...c, redteam: true }))} />
      ) : null}
      {tab === "drift" ? (
        <DriftAct onComplete={() => setCompleted((c) => ({ ...c, drift: true }))} />
      ) : null}
      {tab === "mandates" ? (
        <MandateAct onExit={onExit} onComplete={() => setCompleted((c) => ({ ...c, mandates: true }))} />
      ) : null}

      <Dock
        items={DEMO_NAV.map((n) => {
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
