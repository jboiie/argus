import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { computeFalsePositiveCost, driftCauseBreakdown, driftIncidentsOverTime } from "../lib/data";
import type { DriftIncident, Run } from "../lib/types";
import { Badge, Empty, Metric, Panel, SectionTitle, Untrusted } from "../components/ui";
import { Conversation } from "../components/Conversation";
import { RunSelector } from "../components/RunSelector";

const TOOLTIP = {
  background: "#131c2e",
  border: "1px solid #22304a",
  borderRadius: 8,
  color: "#e6edf7",
};

export function Drift({ incidents, runs }: { incidents: DriftIncident[]; runs: Run[] }) {
  const [runId, setRunId] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const scoped = useMemo(
    () => (runId ? incidents.filter((i) => i.run_id === runId) : incidents),
    [incidents, runId],
  );

  const flagged = scoped.filter((i) => i.flagged);
  const erroredCount = scoped.filter((i) => i.check_status === "errored").length;
  const timeline = useMemo(() => driftIncidentsOverTime(scoped), [scoped]);
  const causes = useMemo(() => driftCauseBreakdown(scoped), [scoped]);
  const cost = useMemo(() => computeFalsePositiveCost(scoped), [scoped]);

  const row = flagged.find((i) => i.incident_id === selected) ?? flagged[0];

  if (incidents.length === 0)
    return <Empty>No drift incidents logged yet — run <code>drift/sampler.py</code>.</Empty>;

  return (
    <div className="space-y-6">
      <RunSelector runs={runs.filter((r) => r.run_type === "drift_sample")} value={runId} onChange={(v) => { setRunId(v); setSelected(null); }} />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Checks run" value={scoped.length} />
        <Metric label="Flagged" value={flagged.length} tone={flagged.length ? "errored" : "default"} />
        <Metric
          label="Flag rate"
          value={scoped.length ? `${((flagged.length / scoped.length) * 100).toFixed(1)}%` : "—"}
        />
        <Metric label="Errored" value={erroredCount} hint="Never completed — flagged is null, not false" />
      </div>

      <Panel>
        <SectionTitle sub="Total checks vs. flagged, per day. Meant to be read across build days, not within one batch.">
          Incidents over time
        </SectionTitle>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timeline} margin={{ top: 8, right: 12, left: -16, bottom: 4 }}>
              <CartesianGrid stroke="#22304a" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="day" tick={{ fill: "#93a4bf", fontSize: 11 }} tickLine={false} />
              <YAxis tick={{ fill: "#93a4bf", fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip contentStyle={TOOLTIP} />
              <Line type="monotone" dataKey="total" stroke="#38bdf8" strokeWidth={2} dot={false} name="checks" />
              <Line type="monotone" dataKey="flagged" stroke="#fbbf24" strokeWidth={2} dot={false} name="flagged" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      {causes.length > 0 ? (
        <Panel>
          <SectionTitle sub="Flagged only. Classified rule-based, not by an LLM: stale_ground_truth is a git-history lookup against the ground-truth file's real past values; fabrication is a value that never existed.">
            Drift cause
          </SectionTitle>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={causes} layout="vertical" margin={{ top: 4, right: 16, left: 40, bottom: 4 }}>
                <CartesianGrid stroke="#22304a" strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fill: "#93a4bf", fontSize: 11 }} allowDecimals={false} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="cause" tick={{ fill: "#93a4bf", fontSize: 11 }} tickLine={false} axisLine={false} width={130} />
                <Tooltip contentStyle={TOOLTIP} cursor={{ fill: "#182238" }} />
                <Bar dataKey="count" fill="#c084fc" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      ) : null}

      <Panel>
        <SectionTitle>False-positive cost</SectionTitle>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Flagged" value={cost.total_flagged} />
          <Metric label="Reviewed" value={cost.reviewed} />
          <Metric label="Confirmed drift" value={cost.true_positives} tone="defended" />
          <Metric
            label="False-positive rate"
            value={cost.false_positive_rate === null ? "n/a" : `${Math.round(cost.false_positive_rate * 100)}%`}
            tone="errored"
          />
        </div>
        {cost.pending_review > 0 ? (
          <p className="mt-3 text-xs text-ink-dim">
            {cost.pending_review} flagged incident(s) still awaiting review, so the rate is computed
            over the reviewed subset only.
          </p>
        ) : null}
        <p className="mt-3 text-xs leading-relaxed text-ink-dim">
          Review cost is modelled at 1 unit per flagged incident. The assumption that a missed drift
          costs several times more is stated explicitly and is <strong>not</strong> measured — there
          is no ground truth on what should have been flagged but wasn't. It is the stated reason
          both thresholds lean toward over-flagging.
        </p>
      </Panel>

      <Panel>
        <SectionTitle>Audit trail</SectionTitle>
        {flagged.length === 0 ? (
          <p className="text-sm text-ink-dim">No flagged incidents to inspect in this run.</p>
        ) : (
          <>
            <select
              className="w-full rounded-lg border border-edge bg-ground px-3 py-2 text-sm text-ink outline-none focus:border-accent"
              value={row?.incident_id ?? ""}
              onChange={(e) => setSelected(e.target.value)}
            >
              {flagged.map((i) => (
                <option key={i.incident_id} value={i.incident_id}>
                  {i.check_type} · {i.ground_truth_ref ?? "(uncovered)"} · {i.question.slice(0, 60)}
                </option>
              ))}
            </select>

            {row ? (
              <div className="mt-4 rounded-lg border border-edge bg-ground/40 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="font-semibold text-ink">
                      {row.check_type} · <code className="text-accent-dim">{row.ground_truth_ref ?? "no ref"}</code>
                    </div>
                    <div className="text-xs text-ink-dim">
                      cause: {row.drift_cause ?? "unclassified"}
                      {row.score !== null ? ` · score: ${row.score.toFixed(2)}` : ""} · review:{" "}
                      {row.is_false_positive === false
                        ? "confirmed drift"
                        : row.is_false_positive
                          ? "false positive"
                          : "unreviewed"}
                    </div>
                  </div>
                  {row.severity ? <Badge tone={row.severity}>{row.severity}</Badge> : null}
                </div>
                <Untrusted label="Question" value={row.question} />
                <div className="grid gap-3 md:grid-cols-2">
                  <Untrusted label="Expected (ground truth at check time)" value={row.expected} />
                  <Untrusted label="Actual (agent answer)" value={row.actual} />
                </div>
                <Conversation sessionId={row.session_id} />
              </div>
            ) : null}
          </>
        )}
      </Panel>
    </div>
  );
}
