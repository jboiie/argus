import { useRef, useState } from "react";
import { Panel, Stamp, Stat, StatStrip } from "../../components/ui";
import { sleep, typeInto, type RunCtl } from "../../lib/demoEngine";
import { Controls } from "./RedTeamAct";

const BEAT_MS = 550;

export function DriftAct() {
  const runId = useRef(0);
  const pausedRef = useRef(false);
  const [paused, setPaused] = useState(false);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);

  const [priceChanged, setPriceChanged] = useState(false);
  const [driftStep, setDriftStep] = useState(0);
  const [driftAnswer, setDriftAnswer] = useState("");
  const [driftVerdict, setDriftVerdict] = useState<string | null>(null);
  const [freshAnswer, setFreshAnswer] = useState("");
  const [freshOk, setFreshOk] = useState(false);

  async function play() {
    const myRun = ++runId.current;
    const ctl: RunCtl = { isStale: () => runId.current !== myRun, isPaused: () => pausedRef.current };

    pausedRef.current = false;
    setPaused(false);
    setRunning(true);
    setDone(false);
    setPriceChanged(false);
    setDriftStep(0);
    setDriftAnswer("");
    setDriftVerdict(null);
    setFreshAnswer("");
    setFreshOk(false);

    await sleep(BEAT_MS, ctl);
    if (ctl.isStale()) return;
    setPriceChanged(true);
    await sleep(700, ctl);
    if (ctl.isStale()) return;
    setDriftStep(1);
    await typeInto(setDriftAnswer, "The Merino Wool Beanie costs Rs.899.", ctl);
    await sleep(400, ctl);
    if (ctl.isStale()) return;
    setDriftVerdict("flagged");
    await sleep(BEAT_MS, ctl);
    if (ctl.isStale()) return;
    setDriftStep(2);
    await typeInto(setFreshAnswer, "The Merino Wool Beanie costs Rs.799.", ctl);
    await sleep(400, ctl);
    if (ctl.isStale()) return;
    setFreshOk(true);
    await sleep(400, ctl);

    if (!ctl.isStale()) {
      setRunning(false);
      setDone(true);
    }
  }

  function togglePause() {
    pausedRef.current = !pausedRef.current;
    setPaused(pausedRef.current);
  }

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-mono text-sm font-semibold tracking-[0.14em] text-brass uppercase">
          Act II · Drift sentinel
        </h2>
        <Controls running={running} paused={paused} done={done} onPlay={play} onPause={togglePause} />
      </div>

      <StatStrip>
        <Stat label="Checks" value={driftStep > 0 ? (driftStep > 1 ? 2 : 1) : 0} />
        <Stat label="Flagged" value={driftVerdict ? 1 : 0} tone={driftVerdict ? "errored" : "default"} />
        <Stat label="Flag rate" value={driftStep > 1 ? "50%" : "—"} tone="brand" />
        <Stat label="Errored" value={0} />
      </StatStrip>

      {!running && !done ? (
        <p className="mt-4 max-w-lg text-sm leading-relaxed text-ink-2">
          A price changes mid-session. A previously-logged answer gets re-checked against the new ground truth
          and flagged stale; a fresh re-ask in the same session reflects the change immediately. Press Run.
        </p>
      ) : null}

      {priceChanged ? (
        <Panel className="mt-4">
          <p className="font-mono text-sm">
            <span className="text-ink-3 line-through">Merino Wool Beanie: Rs.899</span>
            <span className="mx-2 text-ink-3">→</span>
            <span className="text-brass">Rs.799</span>
          </p>
          {driftStep >= 1 ? (
            <div className="mt-4 space-y-1.5 font-mono text-sm">
              <p className="text-2xs text-ink-3 uppercase tracking-[0.1em]">Cached answer, re-checked</p>
              <p className="text-ink">{driftAnswer}</p>
              {driftVerdict ? (
                <div className="mt-1 flex items-center gap-2">
                  <Stamp verdict="flagged" />
                  <span className="text-2xs text-ink-3">stale_ground_truth · critical</span>
                </div>
              ) : null}
            </div>
          ) : null}
          {driftStep >= 2 ? (
            <div className="mt-5 space-y-1.5 border-t border-rule pt-4 font-mono text-sm">
              <p className="text-2xs text-ink-3 uppercase tracking-[0.1em]">Fresh re-ask, same session</p>
              <p className="text-ink">{freshAnswer}</p>
              {freshOk ? (
                <div className="mt-1 flex items-center gap-2">
                  <Stamp verdict="defended" />
                  <span className="text-2xs text-ink-3">not flagged — reflects new ground truth</span>
                </div>
              ) : null}
            </div>
          ) : null}
        </Panel>
      ) : null}
    </div>
  );
}
