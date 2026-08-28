import type { Run } from "../lib/types";
import { Select } from "./ui";

/**
 * Runs differ in simulator model, code version, and how much API quota was
 * left when they executed. Blending every run ever logged into one number is
 * not something a reader can interpret, so a view can be scoped to one.
 */
export function RunSelector({
  runs,
  value,
  onChange,
}: {
  runs: Run[];
  value: string | null;
  onChange: (runId: string | null) => void;
}) {
  if (runs.length === 0) return null;
  return (
    <div className="flex items-center gap-2">
      <span className="text-2xs font-medium tracking-[0.08em] text-ink-3 uppercase">Run</span>
      <Select
        label="Filter by run"
        className="min-w-72"
        value={value ?? ""}
        onChange={(v) => onChange(v || null)}
      >
        <option value="">All runs (cumulative)</option>
        {runs.map((r) => (
          <option key={r.run_id} value={r.run_id}>
            {r.started_at.slice(0, 16).replace("T", " ")} — {r.label}
          </option>
        ))}
      </Select>
    </div>
  );
}
