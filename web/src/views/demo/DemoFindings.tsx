import { Panel, Stamp, Stat, StatStrip } from "../../components/ui";
import type { RedTeamRow } from "./RedTeamAct";
import type { DriftUpdate } from "./DriftAct";
import type { MandateUpdate } from "./MandateAct";

/* Live rollup of whatever the other three acts have produced so far this
 * session - not a fourth scripted act of its own. Re-renders on every
 * onUpdate() call from Red Team / Drift / Mandates (lifted into
 * Demo/index.tsx), so it's current the instant a verdict lands, not just
 * once an act finishes. */

function Empty({ hint }: { hint: string }) {
  return <p className="mt-3 text-sm text-ink-3">{hint}</p>;
}

export function DemoFindings({
  redteam,
  drift,
  mandate,
}: {
  redteam: RedTeamRow[];
  drift: DriftUpdate | null;
  mandate: MandateUpdate;
}) {
  const defended = redteam.filter((r) => r.outcome === "defended").length;
  const bypassed = redteam.filter((r) => r.outcome === "bypassed").length;
  const scored = defended + bypassed;

  const nothingYet = redteam.length === 0 && !drift && !mandate.denied && !mandate.authorized;

  return (
    <div className="mx-auto max-w-4xl py-6">
      <div className="mb-8">
        <span className="font-mono text-2xs tracking-[0.2em] text-brass uppercase">Findings · live</span>
        <h2 className="mt-2 font-serif text-4xl text-ink">Whatever's run so far.</h2>
        <p className="mt-2 max-w-xl text-sm text-ink-2">
          Updates the instant a simulated result lands — no need to finish an act, or run them in order.
        </p>
      </div>

      {nothingYet ? (
        <Panel>
          <p className="text-sm text-ink-2">
            Nothing simulated yet. Run Red Team, Drift, or Mandates and come back — this page fills in live.
          </p>
        </Panel>
      ) : null}

      <section className="mb-8">
        <h3 className="font-mono text-xs font-semibold tracking-[0.14em] text-brass uppercase">Red team</h3>
        {redteam.length === 0 ? (
          <Empty hint="No attacks run yet." />
        ) : (
          <>
            <StatStrip>
              <Stat label="Attempts" value={redteam.length} />
              <Stat label="Defended" value={defended} tone="defended" />
              <Stat label="Bypassed" value={bypassed} tone={bypassed ? "bypassed" : "default"} />
              <Stat label="Sample ASR" value={scored ? `${Math.round((bypassed / scored) * 100)}%` : "—"} tone="brand" />
            </StatStrip>
            <div className="mt-3 space-y-2">
              {redteam.map((r, i) => (
                <div key={i} className="flex items-center justify-between border-b border-rule-soft py-1.5 text-sm">
                  <span className="text-ink-2">
                    {r.vuln} <span className="font-mono text-2xs text-ink-3">{r.type}</span>
                  </span>
                  <Stamp verdict={r.outcome} />
                </div>
              ))}
            </div>
          </>
        )}
      </section>

      <section className="mb-8">
        <h3 className="font-mono text-xs font-semibold tracking-[0.14em] text-brass uppercase">Drift sentinel</h3>
        {!drift ? (
          <Empty hint="No drift check run yet." />
        ) : (
          <Panel className="mt-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="font-mono text-sm text-ink">{drift.category}</p>
                <p className="font-mono text-2xs text-ink-3">{drift.checkType}</p>
              </div>
              <div className="flex gap-6 text-right">
                <div>
                  <div className="tnum text-lg font-bold text-ink">{drift.checks}</div>
                  <div className="font-mono text-2xs text-ink-3 uppercase">checks</div>
                </div>
                <div>
                  <div className="tnum text-lg font-bold text-caution">{drift.flagged}</div>
                  <div className="font-mono text-2xs text-ink-3 uppercase">flagged</div>
                </div>
              </div>
            </div>
            {drift.lastVerdict ? (
              <div className="mt-3 border-t border-rule pt-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Stamp verdict={drift.lastVerdict.tag} />
                  {drift.lastVerdict.cause ? (
                    <span className="text-2xs text-ink-3">
                      {[drift.lastVerdict.cause, drift.lastVerdict.severity].filter(Boolean).join(" · ")}
                    </span>
                  ) : null}
                </div>
                <p className="mt-1 text-2xs text-ink-3">{drift.lastVerdict.note}</p>
              </div>
            ) : null}
          </Panel>
        )}
      </section>

      <section>
        <h3 className="font-mono text-xs font-semibold tracking-[0.14em] text-brass uppercase">Mandate gate</h3>
        {!mandate.denied && !mandate.authorized ? (
          <Empty hint="No mandate scenario run yet." />
        ) : (
          <div className="mt-3 flex flex-wrap gap-6">
            <div className="flex items-center gap-2">
              <span className="font-mono text-2xs text-ink-3 uppercase">Fabricated confirmation</span>
              {mandate.denied ? <Stamp verdict="denied" /> : <span className="text-ink-3">—</span>}
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-2xs text-ink-3 uppercase">Genuine confirmation</span>
              {mandate.authorized ? <Stamp verdict="authorized" /> : <span className="text-ink-3">—</span>}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
