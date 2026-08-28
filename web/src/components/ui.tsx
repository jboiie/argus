import type { ReactNode } from "react";

export function Panel({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-edge bg-panel/70 p-5 shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

export function Metric({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "default" | "bypassed" | "defended" | "errored";
}) {
  const toneClass = {
    default: "text-ink",
    bypassed: "text-bypassed",
    defended: "text-defended",
    errored: "text-errored",
  }[tone];
  return (
    <div className="rounded-xl border border-edge bg-panel/70 px-4 py-3" title={hint}>
      <div className="text-[11px] font-medium uppercase tracking-wider text-ink-dim">
        {label}
      </div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${toneClass}`}>{value}</div>
      {hint ? <div className="mt-1 text-xs leading-snug text-ink-dim">{hint}</div> : null}
    </div>
  );
}

const BADGE_TONES: Record<string, string> = {
  bypassed: "border-bypassed/40 bg-bypassed/10 text-bypassed",
  defended: "border-defended/40 bg-defended/10 text-defended",
  errored: "border-errored/40 bg-errored/10 text-errored",
  critical: "border-bypassed/40 bg-bypassed/10 text-bypassed",
  moderate: "border-errored/40 bg-errored/10 text-errored",
  authorized: "border-defended/40 bg-defended/10 text-defended",
  denied: "border-errored/40 bg-errored/10 text-errored",
  accent: "border-accent/40 bg-accent/10 text-accent",
  violet: "border-violet/40 bg-violet/10 text-violet",
  neutral: "border-edge bg-panel-2 text-ink-dim",
};

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${
        BADGE_TONES[tone] ?? BADGE_TONES.neutral
      }`}
    >
      {children}
    </span>
  );
}

/**
 * Renders attacker-influenced text as literal, non-interpreted content.
 *
 * Attack prompts, agent responses, judge reasoning and session turns are
 * written by an adversarial generator or by a model answering one, and a
 * prompt-injection payload is routinely shaped to look like markup. React
 * escapes by default and this app never uses dangerouslySetInnerHTML - the
 * monospace pre-wrap block is what makes that visible to a reader too.
 */
export function Untrusted({ label, value }: { label: string; value: unknown }) {
  const text =
    value === null || value === undefined || String(value).trim() === ""
      ? "(empty)"
      : String(value);
  return (
    <div className="mt-3">
      <div className="mb-1 text-[11px] font-medium uppercase tracking-wider text-ink-dim">
        {label}
      </div>
      <pre className="untrusted max-h-64 overflow-auto rounded-lg border border-edge bg-ground/80 p-3 text-[13px] leading-relaxed text-ink/90">
        {text}
      </pre>
    </div>
  );
}

export function SectionTitle({ children, sub }: { children: ReactNode; sub?: string }) {
  return (
    <div className="mb-3">
      <h2 className="text-lg font-semibold text-ink">{children}</h2>
      {sub ? <p className="mt-1 text-sm leading-relaxed text-ink-dim">{sub}</p> : null}
    </div>
  );
}

export function Note({
  children,
  tone = "accent",
}: {
  children: ReactNode;
  tone?: "accent" | "warn" | "bad";
}) {
  const cls = {
    accent: "border-accent/30 bg-accent/5 text-ink/90",
    warn: "border-errored/30 bg-errored/5 text-ink/90",
    bad: "border-bypassed/30 bg-bypassed/5 text-ink/90",
  }[tone];
  return (
    <div className={`rounded-lg border p-4 text-sm leading-relaxed ${cls}`}>{children}</div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <Panel>
      <p className="text-sm text-ink-dim">{children}</p>
    </Panel>
  );
}
