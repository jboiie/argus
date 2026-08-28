import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { computeFalsePositiveCost, driftCauseBreakdown, driftIncidentsOverTime } from "../lib/data";
import type { DriftIncident, Run } from "../lib/types";
import {
  Empty,
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
    <div className="space-y-4">
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

      <div className="grid items-start gap-4 xl:grid-cols-2">
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
