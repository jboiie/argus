import { useMemo, useState } from "react";
import { computeAsrByCategory } from "../lib/data";
import type { AttackEvent, Run } from "../lib/types";
import {
  Empty,
  Note,
  Panel,
  ScrollX,
  Select,
  Stamp,
  Stat,
  StatStrip,
  Td,
  Th,
  Untrusted,
} from "../components/ui";
import { Conversation } from "../components/Conversation";
import { RunSelector } from "../components/RunSelector";

const RANK: Record<string, number> = { bypassed: 0, errored: 1, defended: 2 };

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

  const ordered = useMemo(
    () =>
      [...scoped].sort(
        (a, b) =>
          (RANK[a.outcome] ?? 3) - (RANK[b.outcome] ?? 3) ||
          a.vulnerability.localeCompare(b.vulnerability),
      ),
    [scoped],
  );
  const row = ordered.find((e) => e.attack_id === selected) ?? ordered[0];

  if (events.length === 0)
    return <Empty>No attack events logged yet — run redteam/run_full.py</Empty>;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <RunSelector
          runs={runs.filter((r) => r.run_type === "redteam")}
          value={runId}
          onChange={(v) => {
            setRunId(v);
            setSelected(null);
          }}
        />
      </div>

      <StatStrip>
        <Stat label="Attempts" value={bypassed + defended + errored} />
        <Stat
          label="Scored"
          value={scored}
          hint="Errored attempts never got a real answer, so they are excluded from the rate"
        />
        <Stat label="Bypassed" value={bypassed} tone={bypassed ? "bypassed" : "default"} />
        <Stat label="Attack success rate" value={`${overall.toFixed(2)}%`} tone="brand" />
      </StatStrip>

      {bypassed > 0 ? (
        <Note tone="warn">
          <strong className="text-ink">Read every bypass before believing it.</strong> DeepTeam's
          framework criteria carry no knowledge of this agent's scope, so a correct refusal can
          score as a failure — logged examples include the agent declining an off-topic question and
          being marked down for it. The four commerce vulnerabilities don't have this problem: their
          criteria are written against this repo's own catalog, policies and mandate rules.
        </Note>
      ) : null}

      <Panel title="Attack success rate by category" sub="One row per vulnerability type, labelled with its OWASP ASI code.">
        <ScrollX label="Attack success rate by category">
          <table className="w-full min-w-[760px] border-collapse">
            <caption className="sr-only">
              Attack success rate per vulnerability type with attempts, bypassed, defended and
              errored counts
            </caption>
            <thead>
              <tr>
                <Th>ASI</Th>
                <Th>Vulnerability</Th>
                <Th>Type</Th>
                <Th align="right" title="Attempts">Att</Th>
                <Th align="right" title="Bypassed">Byp</Th>
                <Th align="right" title="Defended">Def</Th>
                <Th align="right" title="Errored">Err</Th>
                <Th>ASR</Th>
              </tr>
            </thead>
            <tbody>
              {asr.map((r) => (
                <tr
                  key={`${r.vulnerability}-${r.vulnerability_type}`}
                  className="transition-colors duration-150 hover:bg-chrome-2"
                >
                  <Td mono className="whitespace-nowrap text-ink-3">{r.asi_category ?? "—"}</Td>
                  <Td className="text-ink">{r.vulnerability}</Td>
                  <Td mono className="text-ink-3">{r.vulnerability_type}</Td>
                  <Td align="right" mono>{r.attempts}</Td>
                  <Td align="right" mono className={r.bypassed ? "text-signal-soft" : "text-ink-3"}>
                    {r.bypassed}
                  </Td>
                  <Td align="right" mono className="text-verdict-soft">{r.defended}</Td>
                  <Td align="right" mono className={r.errored ? "text-caution-soft" : "text-ink-3"}>
                    {r.errored}
                  </Td>
                  <Td>
                    <div
                      className="flex items-center gap-2"
                      role="img"
                      aria-label={`Attack success rate ${r.asr_pct.toFixed(1)} percent`}
                    >
                      <div className="h-1 w-16 overflow-hidden bg-rule">
                        <div
                          className={`h-full ${r.asr_pct ? "bg-signal" : "bg-verdict"}`}
                          style={{ width: `${Math.max(r.asr_pct, r.asr_pct ? 6 : 3)}%` }}
                        />
                      </div>
                      <span className="tnum text-2xs text-ink-3">{r.asr_pct.toFixed(1)}%</span>
                    </div>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollX>
      </Panel>

      <Panel
        title="Audit trail"
        sub="Full prompt, response and judge reasoning behind any single attempt. Bypasses listed first."
        right={
          <Select
            label="Select an attack attempt to inspect"
            className="max-w-md min-w-64"
            value={row?.attack_id ?? ""}
            onChange={setSelected}
          >
            {ordered.map((e) => (
              <option key={e.attack_id} value={e.attack_id}>
                {e.outcome.toUpperCase()} · {e.vulnerability}/{e.vulnerability_type} ·{" "}
                {(e.prompt ?? "").replace(/\s+/g, " ").slice(0, 48)}
              </option>
            ))}
          </Select>
        }
      >
        {row ? (
          <>
            <div className="mb-3.5 flex flex-wrap items-center justify-between gap-2 border-b border-rule pb-3">
              <div>
                <div className="text-sm font-semibold text-ink">
                  {row.vulnerability} / {row.vulnerability_type}
                </div>
                <div className="tnum mt-1 text-2xs text-ink-3">
                  {row.asi_category ?? "no ASI mapping"} · method: {row.attack_method ?? "n/a"}
                </div>
              </div>
              <Stamp verdict={row.outcome} />
            </div>
            <div className="grid gap-3 lg:grid-cols-2">
              <Untrusted label="Attack prompt" value={row.prompt} />
              <Untrusted label="Agent response" value={row.response} />
            </div>
            <div className="mt-3">
              <Untrusted label="Judge reasoning" value={row.reason} />
            </div>
            <Conversation sessionId={row.session_id} />
          </>
        ) : null}
      </Panel>
    </div>
  );
}
