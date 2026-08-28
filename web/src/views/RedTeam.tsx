import { useMemo, useState } from "react";
import { computeAsrByCategory } from "../lib/data";
import type { AttackEvent, Run } from "../lib/types";
import { Badge, Empty, Metric, Note, Panel, SectionTitle, Untrusted } from "../components/ui";
import { Conversation } from "../components/Conversation";
import { RunSelector } from "../components/RunSelector";

const OUTCOME_RANK: Record<string, number> = { bypassed: 0, errored: 1, defended: 2 };

export function RedTeam({ events, runs }: { events: AttackEvent[]; runs: Run[] }) {
  const [runId, setRunId] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const scoped = useMemo(
    () => (runId ? events.filter((e) => e.run_id === runId) : events),
    [events, runId],
  );
  const asr = useMemo(() => computeAsrByCategory(scoped), [scoped]);

  const bypassed = asr.reduce((n, r) => n + r.bypassed, 0);
  const defended = asr.reduce((n, r) => n + r.defended, 0);
  const errored = asr.reduce((n, r) => n + r.errored, 0);
  const scored = bypassed + defended;
  const overall = scored ? (bypassed / scored) * 100 : 0;

  // Bypasses first - they are what anyone opens this page to read.
  const ordered = useMemo(
    () =>
      [...scoped].sort(
        (a, b) =>
          (OUTCOME_RANK[a.outcome] ?? 3) - (OUTCOME_RANK[b.outcome] ?? 3) ||
          a.vulnerability.localeCompare(b.vulnerability),
      ),
    [scoped],
  );
  const row = ordered.find((e) => e.attack_id === selected) ?? ordered[0];

  if (events.length === 0)
    return <Empty>No attack events logged yet — run <code>redteam/run_full.py</code>.</Empty>;

  return (
    <div className="space-y-6">
      <RunSelector runs={runs.filter((r) => r.run_type === "redteam")} value={runId} onChange={(v) => { setRunId(v); setSelected(null); }} />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Attempts" value={bypassed + defended + errored} />
        <Metric label="Scored" value={scored} hint="Errored attempts are excluded from the rate — they never got a real answer" />
        <Metric label="Bypassed" value={bypassed} tone={bypassed ? "bypassed" : "default"} />
        <Metric label="Attack Success Rate" value={`${overall.toFixed(2)}%`} />
      </div>

      {bypassed > 0 ? (
        <Note tone="warn">
          <strong>Read every bypass before believing it.</strong> DeepTeam's framework criteria
          carry no knowledge of this agent's scope, so a correct refusal can score as a failure —
          logged examples include the agent declining an off-topic question and being marked down
          for it. The four commerce vulnerabilities don't have this problem: their criteria are
          written against this repo's own catalog, policies and mandate rules.
        </Note>
      ) : null}

      <Panel>
        <SectionTitle sub="One row per vulnerability type, each labelled with its OWASP ASI code.">
          Attack Success Rate by category
        </SectionTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-edge text-left text-[11px] uppercase tracking-wider text-ink-dim">
                <th className="py-2 pr-3 font-medium">ASI</th>
                <th className="py-2 pr-3 font-medium">Vulnerability</th>
                <th className="py-2 pr-3 font-medium">Type</th>
                <th className="py-2 pr-3 text-right font-medium">Att.</th>
                <th className="py-2 pr-3 text-right font-medium">Byp.</th>
                <th className="py-2 pr-3 text-right font-medium">Def.</th>
                <th className="py-2 pr-3 text-right font-medium">Err.</th>
                <th className="py-2 pl-3 font-medium">ASR</th>
              </tr>
            </thead>
            <tbody>
              {asr.map((r) => (
                <tr
                  key={`${r.vulnerability}-${r.vulnerability_type}`}
                  className="border-b border-edge/40 hover:bg-panel-2/60"
                >
                  <td className="py-2 pr-3 whitespace-nowrap text-ink-dim">{r.asi_category ?? "—"}</td>
                  <td className="py-2 pr-3">{r.vulnerability}</td>
                  <td className="py-2 pr-3 text-ink-dim">{r.vulnerability_type}</td>
                  <td className="py-2 pr-3 text-right tabular-nums">{r.attempts}</td>
                  <td className={`py-2 pr-3 text-right tabular-nums ${r.bypassed ? "text-bypassed" : ""}`}>{r.bypassed}</td>
                  <td className="py-2 pr-3 text-right tabular-nums text-defended">{r.defended}</td>
                  <td className={`py-2 pr-3 text-right tabular-nums ${r.errored ? "text-errored" : "text-ink-dim"}`}>{r.errored}</td>
                  <td className="py-2 pl-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-edge">
                        <div
                          className={`h-full ${r.asr_pct ? "bg-bypassed" : "bg-defended"}`}
                          style={{ width: `${Math.max(r.asr_pct, r.asr_pct ? 4 : 2)}%` }}
                        />
                      </div>
                      <span className="tabular-nums text-xs text-ink-dim">{r.asr_pct.toFixed(1)}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel>
        <SectionTitle sub="Full prompt, response and judge reasoning behind any single attempt.">
          Audit trail
        </SectionTitle>
        <select
          className="w-full rounded-lg border border-edge bg-ground px-3 py-2 text-sm text-ink outline-none focus:border-accent"
          value={row?.attack_id ?? ""}
          onChange={(e) => setSelected(e.target.value)}
        >
          {ordered.map((e) => (
            <option key={e.attack_id} value={e.attack_id}>
              {e.outcome.toUpperCase()} · {e.vulnerability} / {e.vulnerability_type} ·{" "}
              {(e.prompt ?? "").replace(/\s+/g, " ").slice(0, 60)}
            </option>
          ))}
        </select>

        {row ? (
          <div className="mt-4 rounded-lg border border-edge bg-ground/40 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="font-semibold text-ink">
                  {row.vulnerability} / {row.vulnerability_type}
                </div>
                <div className="text-xs text-ink-dim">
                  {row.asi_category ?? "no ASI mapping"} · attack method: {row.attack_method ?? "n/a"}
                </div>
              </div>
              <Badge tone={row.outcome}>{row.outcome}</Badge>
            </div>
            <Untrusted label="Attack prompt" value={row.prompt} />
            <Untrusted label="Agent response" value={row.response} />
            <Untrusted label="Judge reasoning" value={row.reason} />
            <Conversation sessionId={row.session_id} />
          </div>
        ) : null}
      </Panel>
    </div>
  );
}
