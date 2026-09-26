import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { computeFalsePositiveCost, driftCauseBreakdown, driftIncidentsOverTime, fetchLayaDriftScores } from "../lib/data";
import { OPERATING_POINTS, SWEEP_CURVE, TEST_CLAIMS, TEST_COMPARISON } from "../lib/layaEval";
import type { DriftIncident, LayaDriftScore, Run } from "../lib/types";
import {
  Empty,
  Note,
  Panel,
  Select,
  Stat,
  StatStrip,
  Tag,
  Td,
  Th,
  Untrusted,
} from "../components/ui";
import { Conversation } from "../components/Conversation";
import { RunSelector } from "../components/RunSelector";

const TOOLTIP = {
  background: "#141a24",
  border: "1px solid #262f3d",
  borderRadius: 3,
  color: "#e7e9ec",
  fontSize: 12,
  fontFamily: '"IBM Plex Mono", monospace',
};
const AXIS = { fill: "#67717f", fontSize: 11, fontFamily: '"IBM Plex Mono", monospace' };

/** A line chart needs a trend to show. Below four points there is no trend,
 *  only noise dressed as one - the guidance is explicit that a stat/table
 *  beats a line here, and an almost-empty chart reads as missing data. */
const MIN_POINTS_FOR_LINE = 4;

export function Drift({ incidents, runs }: { incidents: DriftIncident[]; runs: Run[] }) {
  const [runId, setRunId] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [layaScores, setLayaScores] = useState<LayaDriftScore[]>([]);

  // Own effect, own state - laya_drift_scores may not exist yet
  // (scripts/migrate_004_laya_drift_scores.sql not applied), and
  // fetchLayaDriftScores() already degrades to [] rather than throwing,
  // so this panel alone shows "no data yet" instead of breaking the page.
  useEffect(() => {
    fetchLayaDriftScores().then(setLayaScores);
  }, []);

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
    return <Empty>No drift incidents logged yet — run drift/sampler.py</Empty>;

  return (
    <div className="space-y-5">
      <RunSelector
        runs={runs.filter((r) => r.run_type === "drift_sample")}
        value={runId}
        onChange={(v) => {
          setRunId(v);
          setSelected(null);
        }}
      />

      <StatStrip>
        <Stat label="Checks run" value={scoped.length} />
        <Stat label="Flagged" value={flagged.length} tone={flagged.length ? "errored" : "default"} />
        <Stat
          label="Flag rate"
          value={scoped.length ? `${((flagged.length / scoped.length) * 100).toFixed(1)}%` : "—"}
          tone="brand"
        />
        <Stat
          label="Errored"
          value={erroredCount}
          hint="Never completed — flagged is null, not false"
        />
      </StatStrip>

      <Note>
        Every check here re-verifies a previous or adjacent claim against real ground truth — a
        price, a policy, or three independent samples of a question with no ground truth at all. A
        flagged row means the agent's answer stopped matching reality after it was already live —
        the failure mode a one-time pre-launch test can never catch.
      </Note>

      <div className="grid items-start gap-5 xl:grid-cols-2">
        <Panel
          title="Checks over time"
          sub={
            timeline.length < MIN_POINTS_FOR_LINE
              ? "Too few days for a trend line — shown as a table until there are at least four."
              : "Total checks vs. flagged, per day. Read across build days, not within one batch."
          }
        >
          {timeline.length < MIN_POINTS_FOR_LINE ? (
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Day</Th>
                  <Th align="right">Checks</Th>
                  <Th align="right">Flagged</Th>
                  <Th align="right">Rate</Th>
                </tr>
              </thead>
              <tbody>
                {timeline.map((d) => (
                  <tr key={d.day} className="transition-colors duration-150 hover:bg-chrome-2">
                    <Td mono>{d.day}</Td>
                    <Td align="right" mono>{d.total}</Td>
                    <Td align="right" mono className={d.flagged ? "text-caution-soft" : "text-ink-3"}>
                      {d.flagged}
                    </Td>
                    <Td align="right" mono className="text-ink-3">
                      {((d.flagged / d.total) * 100).toFixed(0)}%
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timeline} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="#262f3d" strokeDasharray="2 4" vertical={false} />
                  <XAxis dataKey="day" tick={AXIS} tickLine={false} axisLine={{ stroke: "#262f3d" }} />
                  <YAxis tick={AXIS} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip contentStyle={TOOLTIP} />
                  <Legend wrapperStyle={{ fontSize: 11, color: "#67717f" }} />
                  {/* Solid vs dashed, not colour alone - colourblind-safe. */}
                  <Line type="monotone" dataKey="total" name="checks" stroke="#c9a227" strokeWidth={2} dot={false} />
                  <Line
                    type="monotone"
                    dataKey="flagged"
                    name="flagged"
                    stroke="#c8322e"
                    strokeWidth={2}
                    strokeDasharray="5 3"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </Panel>

        <Panel
          title="Drift cause"
          sub="Flagged only. Classified rule-based: stale_ground_truth is a git-history lookup against the file's real past values; fabrication is a value that never existed."
        >
          {causes.length === 0 ? (
            <Empty>Nothing flagged in this run.</Empty>
          ) : (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={causes} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#262f3d" strokeDasharray="2 4" horizontal={false} />
                  <XAxis type="number" tick={AXIS} allowDecimals={false} tickLine={false} axisLine={false} />
                  <YAxis
                    type="category"
                    dataKey="cause"
                    tick={AXIS}
                    tickLine={false}
                    axisLine={false}
                    width={140}
                  />
                  <Tooltip contentStyle={TOOLTIP} cursor={{ fill: "#1b2330" }} />
                  <Bar dataKey="count" fill="#8a6f1b" barSize={18} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Panel>
      </div>

      <Panel title="False-positive cost">
        <StatStrip>
          <Stat label="Flagged" value={cost.total_flagged} />
          <Stat label="Reviewed" value={cost.reviewed} />
          <Stat label="Confirmed drift" value={cost.true_positives} tone="defended" />
          <Stat
            label="False-positive rate"
            value={
              cost.false_positive_rate === null
                ? "n/a"
                : `${Math.round(cost.false_positive_rate * 100)}%`
            }
            tone="errored"
          />
        </StatStrip>
        {cost.pending_review > 0 ? (
          <p className="mt-3 text-2xs text-ink-3">
            {cost.pending_review} flagged incident(s) awaiting review — the rate is computed over the
            reviewed subset only.
          </p>
        ) : null}
        <p className="mt-2 text-2xs leading-relaxed text-ink-3">
          Review cost is modelled at 1 unit per flagged incident. The assumption that a missed drift
          costs several times more is stated explicitly and is <strong>not</strong> measured — there
          is no ground truth on what should have been flagged but wasn't. It is the stated reason
          both thresholds lean toward over-flagging.
        </p>
      </Panel>

      <Panel
        title="Laya cascade"
        sub="Step 3/4 offline eval (PROJECT_DESC.md's 'Laya cascade' section) - fixed numbers from a one-time run over saved Laya/RAGAS scores, plus live sampler activity below once LAYA_CASCADE_ENABLED is on and the migration is applied."
      >
        <div className="grid gap-5 xl:grid-cols-2">
          <div>
            <h4 className="mb-2 text-2xs font-semibold tracking-[0.08em] text-ink-3 uppercase">
              Sweep-split threshold curve (134 rows)
            </h4>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={SWEEP_CURVE} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="#262f3d" strokeDasharray="2 4" vertical={false} />
                  <XAxis dataKey="t" tick={AXIS} tickLine={false} axisLine={{ stroke: "#262f3d" }} />
                  <YAxis tick={AXIS} tickLine={false} axisLine={false} domain={[0.7, 0.95]} />
                  <Tooltip contentStyle={TOOLTIP} />
                  <Line type="monotone" dataKey="balancedAccuracy" name="balanced accuracy" stroke="#c9a227" strokeWidth={2} dot={false} />
                  <ReferenceDot
                    x={OPERATING_POINTS.cost.t} y={SWEEP_CURVE[0].balancedAccuracy}
                    r={5} fill="#5fb0e0" stroke="none" label={{ value: "cost", position: "top", fill: "#5fb0e0", fontSize: 11 }}
                  />
                  <ReferenceDot
                    x={OPERATING_POINTS.accuracy.t}
                    y={SWEEP_CURVE.find((p) => p.t === OPERATING_POINTS.accuracy.t)?.balancedAccuracy}
                    r={5} fill="#c8322e" stroke="none" label={{ value: "accuracy", position: "top", fill: "#c8322e", fontSize: 11 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-2 text-2xs text-ink-3">
              Cost point (t=0.50, blue) decides every row alone. Accuracy point (t=0.80, red) is the
              sweep curve's balanced-accuracy peak, chosen after seeing this curve.
            </p>
          </div>

          <div>
            <h4 className="mb-2 text-2xs font-semibold tracking-[0.08em] text-ink-3 uppercase">
              Test-split comparison ({TEST_CLAIMS} claims, 84 rows, run once)
            </h4>
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <Th>Method</Th>
                  <Th align="right">Bal. acc.</Th>
                  <Th align="right">Faithful P/R</Th>
                  <Th align="right">Unfaithful P/R</Th>
                </tr>
              </thead>
              <tbody>
                {TEST_COMPARISON.map((row) => (
                  <tr key={row.method} className="transition-colors duration-150 hover:bg-chrome-2">
                    <Td>{row.method}</Td>
                    <Td align="right" mono>{row.balancedAccuracy.toFixed(4)}</Td>
                    <Td align="right" mono>{row.faithfulPrecision.toFixed(2)}/{row.faithfulRecall.toFixed(2)}</Td>
                    <Td align="right" mono>{row.unfaithfulPrecision.toFixed(2)}/{row.unfaithfulRecall.toFixed(2)}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-2xs leading-relaxed text-ink-3">
              None of the pairwise differences reach p&lt;0.05 by McNemar's exact test on this n=84 -
              read as suggestive, not statistically confirmed.
            </p>
          </div>
        </div>

        <div className="mt-5 border-t border-rule pt-4">
          <h4 className="mb-2 text-2xs font-semibold tracking-[0.08em] text-ink-3 uppercase">
            Live sampler activity
          </h4>
          {layaScores.length === 0 ? (
            <Empty>
              No laya_drift_scores rows yet — apply scripts/migrate_004_laya_drift_scores.sql and run
              drift/sampler.py with LAYA_CASCADE_ENABLED=true.
            </Empty>
          ) : (
            <StatStrip>
              <Stat label="Checks logged" value={layaScores.length} />
              <Stat
                label="Decided by Laya"
                value={`${((layaScores.filter((s) => s.decided_by === "laya").length / layaScores.length) * 100).toFixed(0)}%`}
                tone="brand"
              />
              <Stat
                label="Escalated to RAGAS"
                value={layaScores.filter((s) => s.decided_by === "ragas").length}
              />
              <Stat
                label="Escalation errors"
                value={layaScores.filter((s) => s.errored).length}
                tone={layaScores.some((s) => s.errored) ? "errored" : "default"}
              />
            </StatStrip>
          )}
        </div>
      </Panel>

      <Panel
        title="Audit trail"
        right={
          flagged.length > 0 ? (
            <Select
              label="Select a flagged incident to inspect"
              className="max-w-md min-w-64"
              value={row?.incident_id ?? ""}
              onChange={setSelected}
            >
              {flagged.map((i) => (
                <option key={i.incident_id} value={i.incident_id}>
                  {i.check_type} · {i.ground_truth_ref ?? "(uncovered)"} · {i.question.slice(0, 44)}
                </option>
              ))}
            </Select>
          ) : null
        }
      >
        {flagged.length === 0 ? (
          <Empty>No flagged incidents to inspect in this run.</Empty>
        ) : row ? (
          <>
            <div className="mb-3.5 flex flex-wrap items-center justify-between gap-2 border-b border-rule pb-3">
              <div>
                <div className="text-sm font-semibold text-ink">
                  {row.check_type} ·{" "}
                  <code className="tnum text-brass">{row.ground_truth_ref ?? "no ref"}</code>
                </div>
                <div className="tnum mt-1 text-2xs text-ink-3">
                  cause: {row.drift_cause ?? "unclassified"}
                  {row.score !== null ? ` · score ${row.score.toFixed(2)}` : ""} ·{" "}
                  {row.is_false_positive === false
                    ? "confirmed drift"
                    : row.is_false_positive
                      ? "false positive"
                      : "unreviewed"}
                </div>
              </div>
              {row.severity ? <Tag tone={row.severity}>{row.severity}</Tag> : null}
            </div>
            <Untrusted label="Question" value={row.question} />
            <div className="mt-3 grid gap-3 lg:grid-cols-2">
              <Untrusted label="Expected · ground truth at check time" value={row.expected} />
              <Untrusted label="Actual · agent answer" value={row.actual} />
            </div>
            <Conversation sessionId={row.session_id} />
          </>
        ) : null}
      </Panel>
    </div>
  );
}
