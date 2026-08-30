import { useRef, useState } from "react";
import { Panel, Select, Stamp, Stat, StatStrip } from "../../components/ui";
import { sleep, typeInto, type RunCtl } from "../../lib/demoEngine";
import { Controls } from "./RedTeamAct";

/* One drift check type per real drift_cause the classifier actually
 * produces (drift/classify.py): stale_ground_truth (numeric, a price moved
 * out from under a cached answer), fabrication (faithfulness, a claim that
 * matches no historical version of the policy at all), and inconsistency
 * (self_consistency, three samples of the same question disagree). The
 * dropdown picks which one to demo; picking one plays it immediately. */

export interface VerdictInfo {
  tag: "flagged" | "defended";
  cause?: string;
  severity?: string;
  note: string;
}

export interface DriftUpdate {
  category: string;
  checkType: string;
  checks: number;
  flagged: number;
  lastLabel: string;
  lastVerdict: VerdictInfo | null;
}

type Beat =
  | { kind: "price-diff"; product: string; from: string; to: string }
  | { kind: "line"; label: string; text: string; tone?: "ink" | "brass"; verdict?: VerdictInfo }
  | { kind: "verdict"; verdict: VerdictInfo };

interface Scenario {
  label: string;
  checkType: string;
  intro: string;
  beats: Beat[];
}

const SCENARIOS: Record<string, Scenario> = {
  stale: {
    label: "Stale ground truth",
    checkType: "numeric",
    intro:
      "A price changes mid-session. A previously-logged answer gets re-checked against the new ground truth and flagged stale; a fresh re-ask in the same session reflects the change immediately.",
    beats: [
      { kind: "price-diff", product: "Merino Wool Beanie", from: "Rs.899", to: "Rs.799" },
      {
        kind: "line",
        label: "Cached answer, re-checked",
        text: "The Merino Wool Beanie costs Rs.899.",
        verdict: {
          tag: "flagged",
          cause: "stale_ground_truth",
          severity: "critical",
          note: "matches a prior committed price, not the current one",
        },
      },
      {
        kind: "line",
        label: "Fresh re-ask, same session",
        text: "The Merino Wool Beanie costs Rs.799.",
        verdict: { tag: "defended", note: "not flagged — reflects the new ground truth" },
      },
    ],
  },
  fabrication: {
    label: "Fabrication",
    checkType: "faithfulness",
    intro:
      "A policy claim gets checked against every version the policy file has ever held, past or present. One that matches none of them — not a stale value, an invented one — is fabrication.",
    beats: [
      { kind: "line", label: "Question", text: "What is your international shipping policy?" },
      {
        kind: "line",
        label: "Agent's answer",
        text: "International shipping takes 2 to 3 business days and costs a flat Rs.499.",
        tone: "brass",
        verdict: {
          tag: "flagged",
          cause: "fabrication",
          severity: "moderate",
          note: "no committed version of this policy — current or past — ever said this. Real claim: international shipping is not currently available.",
        },
      },
    ],
  },
  inconsistency: {
    label: "Inconsistency",
    checkType: "self_consistency",
    intro:
      "A question with no ground-truth basis, asked three times. Three genuinely different answers is the hallucination signal itself — there's no single 'expected' value to diff against.",
    beats: [
      {
        kind: "line",
        label: "Question, asked 3 times",
        text: "How long does the Wireless Mechanical Keyboard last on a single charge?",
      },
      {
        kind: "line",
        label: "Sample 1",
        text: "I don't know — the listing doesn't state a battery life for this model.",
        tone: "brass",
      },
      { kind: "line", label: "Sample 2", text: "It lasts approximately 20 hours per charge.", tone: "brass" },
      { kind: "line", label: "Sample 3", text: "Around 8 hours of continuous use.", tone: "brass" },
      {
        kind: "verdict",
        verdict: {
          tag: "flagged",
          cause: "inconsistency",
          note: "agreement 0.33 across 3 samples — below the 0.7 threshold",
        },
      },
    ],
  },
  stale_policy: {
    label: "Stale ground truth — policy",
    checkType: "faithfulness",
    intro:
      "The same stale_ground_truth cause, but from a faithfulness check instead of a numeric one — a policy claim gets checked against the shipping policy's own history, not just its current value.",
    beats: [
      {
        kind: "line",
        label: "Cached answer, re-checked",
        text: "Standard domestic shipping costs 149 rupees per order.",
        verdict: {
          tag: "flagged",
          cause: "stale_ground_truth",
          severity: "moderate",
          note: "matches a prior committed shipping cost, not the current Rs.99",
        },
      },
      {
        kind: "line",
        label: "Fresh re-ask, same session",
        text: "Standard domestic shipping costs Rs.99 per order.",
        verdict: { tag: "defended", note: "not flagged — reflects the current policy" },
      },
    ],
  },
  clean: {
    label: "Clean check (no drift)",
    checkType: "numeric",
    intro:
      "Not every check finds something. Most don't — this is what a normal pass looks like: the agent's answer matches ground truth exactly, nothing flagged.",
    beats: [
      {
        kind: "line",
        label: "Cached answer, re-checked",
        text: "The Portable Bluetooth Speaker costs Rs.2199.",
        verdict: { tag: "defended", note: "matches current ground truth exactly" },
      },
    ],
  },
};

type CategoryKey = keyof typeof SCENARIOS;

export function DriftAct({
  onComplete,
  onUpdate,
}: {
  onComplete?: () => void;
  onUpdate?: (u: DriftUpdate) => void;
}) {
  const runId = useRef(0);
  const pausedRef = useRef(false);
  const [paused, setPaused] = useState(false);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [category, setCategory] = useState<CategoryKey>("stale");

  const [priceDiff, setPriceDiff] = useState<{ product: string; from: string; to: string } | null>(null);
  const [revealed, setRevealed] = useState<{ label: string; text: string; tone: "ink" | "brass"; verdict?: VerdictInfo }[]>([]);
  const [typing, setTyping] = useState<{ label: string; text: string; tone: "ink" | "brass" } | null>(null);
  const [finalVerdict, setFinalVerdict] = useState<VerdictInfo | null>(null);
  const [log, setLog] = useState<{ category: string; label: string; verdict: VerdictInfo }[]>([]);

  async function play(pickedCategory: CategoryKey) {
    const myRun = ++runId.current;
    const ctl: RunCtl = { isStale: () => runId.current !== myRun, isPaused: () => pausedRef.current };

    pausedRef.current = false;
    setPaused(false);
    setRunning(true);
    setDone(false);
    setCategory(pickedCategory);
    setPriceDiff(null);
    setRevealed([]);
    setTyping(null);
    setFinalVerdict(null);

    const scenario = SCENARIOS[pickedCategory];
    let checks = 0;
    let flagged = 0;
    onUpdate?.({ category: scenario.label, checkType: scenario.checkType, checks: 0, flagged: 0, lastLabel: "", lastVerdict: null });

    for (const beat of scenario.beats) {
      if (ctl.isStale()) return;

      if (beat.kind === "price-diff") {
        setPriceDiff({ product: beat.product, from: beat.from, to: beat.to });
        await sleep(700, ctl);
        continue;
      }

      if (beat.kind === "verdict") {
        setFinalVerdict(beat.verdict);
        checks += 1;
        if (beat.verdict.tag === "flagged") flagged += 1;
        setLog((l) => [...l, { category: scenario.label, label: "Result", verdict: beat.verdict }]);
        onUpdate?.({
          category: scenario.label,
          checkType: scenario.checkType,
          checks,
          flagged,
          lastLabel: "Result",
          lastVerdict: beat.verdict,
        });
        await sleep(500, ctl);
        continue;
      }

      const tone = beat.tone ?? "ink";
      setTyping({ label: beat.label, text: "", tone });
      await typeInto((v) => setTyping((t) => (t ? { ...t, text: v } : t)), beat.text, ctl);
      await sleep(150, ctl);
      if (ctl.isStale()) return;
      setRevealed((r) => [...r, { label: beat.label, text: beat.text, tone, verdict: beat.verdict }]);
      setTyping(null);
      if (beat.verdict) {
        checks += 1;
        if (beat.verdict.tag === "flagged") flagged += 1;
        setLog((l) => [...l, { category: scenario.label, label: beat.label, verdict: beat.verdict! }]);
        onUpdate?.({
          category: scenario.label,
          checkType: scenario.checkType,
          checks,
          flagged,
          lastLabel: beat.label,
          lastVerdict: beat.verdict,
        });
      }
      await sleep(beat.verdict ? 550 : 300, ctl);
    }

    if (!ctl.isStale()) {
      setRunning(false);
      setDone(true);
      onComplete?.();
    }
  }

  function togglePause() {
    pausedRef.current = !pausedRef.current;
    setPaused(pausedRef.current);
  }

  const totalChecks = log.length;
  const totalFlagged = log.filter((l) => l.verdict.tag === "flagged").length;

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-mono text-sm font-semibold tracking-[0.14em] text-brass uppercase">
          Act II · Drift sentinel
        </h2>
        <div className="flex items-center gap-3">
          <Select
            label="Drift category to demo"
            value={category}
            onChange={(v) => play(v as CategoryKey)}
            className="min-w-52"
          >
            {Object.entries(SCENARIOS).map(([key, s]) => (
              <option key={key} value={key}>
                {s.label}
              </option>
            ))}
          </Select>
          <Controls running={running} paused={paused} done={done} onPlay={() => play(category)} onPause={togglePause} />
        </div>
      </div>

      <StatStrip>
        <Stat label="Checks" value={totalChecks} />
        <Stat label="Flagged" value={totalFlagged} tone={totalFlagged ? "errored" : "default"} />
        <Stat
          label="Flag rate"
          value={totalChecks ? `${Math.round((totalFlagged / totalChecks) * 100)}%` : "—"}
          tone="brand"
        />
        <Stat label="Check type" value={SCENARIOS[category].checkType} />
      </StatStrip>

      {!running && !done ? (
        <p className="mt-4 max-w-lg text-sm leading-relaxed text-ink-2">{SCENARIOS[category].intro}</p>
      ) : null}

      {priceDiff ? (
        <Panel className="mt-4">
          <p className="font-mono text-sm">
            <span className="text-ink-3 line-through">
              {priceDiff.product}: {priceDiff.from}
            </span>
            <span className="mx-2 text-ink-3">→</span>
            <span className="text-brass">{priceDiff.to}</span>
          </p>
        </Panel>
      ) : null}

      {revealed.length > 0 || typing ? (
        <Panel className={priceDiff ? "mt-3" : "mt-4"}>
          <div className="space-y-4">
            {revealed.map((r, i) => (
              <div key={i} className={i > 0 ? "border-t border-rule pt-4" : ""}>
                <p className="font-mono text-2xs tracking-[0.1em] text-ink-3 uppercase">{r.label}</p>
                <p className={`mt-1 font-mono text-sm ${r.tone === "brass" ? "text-brass" : "text-ink"}`}>
                  {r.text}
                </p>
                {r.verdict ? (
                  <div className="mt-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Stamp verdict={r.verdict.tag} />
                      {r.verdict.cause ? (
                        <span className="text-2xs text-ink-3">
                          {[r.verdict.cause, r.verdict.severity].filter(Boolean).join(" · ")}
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-1 text-2xs text-ink-3">{r.verdict.note}</p>
                  </div>
                ) : null}
              </div>
            ))}
            {typing ? (
              <div className={revealed.length > 0 ? "border-t border-rule pt-4" : ""}>
                <p className="font-mono text-2xs tracking-[0.1em] text-ink-3 uppercase">{typing.label}</p>
                <p className={`mt-1 font-mono text-sm ${typing.tone === "brass" ? "text-brass" : "text-ink"}`}>
                  {typing.text}
                </p>
              </div>
            ) : null}
            {finalVerdict ? (
              <div className="border-t border-rule pt-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Stamp verdict={finalVerdict.tag} />
                  <span className="text-2xs text-ink-3">
                    {[finalVerdict.cause, finalVerdict.severity].filter(Boolean).join(" · ")}
                  </span>
                </div>
                <p className="mt-1.5 text-2xs text-ink-3">{finalVerdict.note}</p>
              </div>
            ) : null}
          </div>
        </Panel>
      ) : null}

      {log.length > 0 ? (
        <>
          <p className="mt-5 mb-1 font-mono text-2xs tracking-[0.1em] text-ink-3 uppercase">
            Check log · {log.length} logged this session
          </p>
          <table className="w-full border-collapse text-sm">
            <tbody>
              {log.map((entry, i) => (
                <tr key={i} className="border-b border-rule-soft">
                  <td className="py-1.5 pr-3 text-ink-2">{entry.category}</td>
                  <td className="py-1.5 pr-3 font-mono text-2xs text-ink-3">
                    {[entry.verdict.cause, entry.verdict.severity].filter(Boolean).join(" · ") || "—"}
                  </td>
                  <td className="py-1.5 text-right">
                    <Stamp verdict={entry.verdict.tag} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : null}
    </div>
  );
}
