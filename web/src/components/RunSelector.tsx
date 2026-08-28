import type { Run } from "../lib/types";

/**
 * Runs differ in simulator model, in code version, and in how much API quota
 * was left when they executed. Blending every run ever logged into one number
 * isn't something a reader can interpret, so the view can be scoped to one.
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
    <div className="flex flex-wrap items-center gap-3">
      <label className="text-[11px] font-medium uppercase tracking-wider text-ink-dim">Run</label>
      <select
        className="min-w-72 rounded-lg border border-edge bg-ground px-3 py-2 text-sm text-ink outline-none focus:border-accent"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value || null)}
      >
        <option value="">All runs (cumulative)</option>
        {runs.map((r) => (
          <option key={r.run_id} value={r.run_id}>
            {r.started_at.slice(0, 16).replace("T", " ")} — {r.label}
          </option>
        ))}
      </select>
    </div>
  );
}
