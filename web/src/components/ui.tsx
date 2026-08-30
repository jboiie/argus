import type { ReactNode } from "react";

/* Console primitives (dark) and Record primitives (light archival stock).
 * The split is the design: the console files things, the record IS the thing. */

export function Panel({
  title,
  sub,
  right,
  children,
  className = "",
}: {
  title?: string;
  sub?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`glow-card rounded-2xl border border-rule bg-chrome ${className}`}>
      {title ? (
        <header className="relative z-[1] flex flex-wrap items-start justify-between gap-3 border-b border-rule px-4 py-3">
          <div>
            <h2 className="font-mono text-xs font-semibold tracking-[0.14em] text-brass uppercase">
              {title}
            </h2>
            {sub ? <p className="mt-1 max-w-3xl text-xs leading-relaxed text-ink-3">{sub}</p> : null}
          </div>
          {right}
        </header>
      ) : null}
      <div className="relative z-[1] p-4">{children}</div>
    </section>
  );
}

/** A record: light archival stock sitting on the dark console.
 *  `tilt` files it by hand rather than by grid — a fraction of a degree, which
 *  is the difference between a document on a desk and a div. */
export function Record({
  children,
  className = "",
  tilt,
}: {
  children: ReactNode;
  className?: string;
  tilt?: "a" | "b" | "c";
}) {
  return (
    <article
      className={`lift rounded-xl bg-stock text-stock-ink ${tilt ? `tilt-${tilt}` : ""} ${className}`}
    >
      {children}
    </article>
  );
}

/** Staggered entrance. One orchestrated sequence on load; `delay` is in ms and
 *  stays small so nothing feels withheld from a reader who came to read. */
export function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <div className={`reveal ${className}`} style={{ animationDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}

/** SIGNATURE — the verdict stamp. */
export function Stamp({ verdict }: { verdict: string }) {
  const tone =
    {
      bypassed: "text-signal",
      paid: "text-signal",
      flagged: "text-caution",
      defended: "text-verdict",
      errored: "text-caution",
      authorized: "text-verdict",
      denied: "text-caution",
      blocked: "text-caution",
      critical: "text-signal",
      moderate: "text-caution",
    }[verdict.toLowerCase()] ?? "text-stock-ink-2";
  return (
    <span className={`stamp text-2xs ${tone}`} role="img" aria-label={`Verdict: ${verdict}`}>
      {verdict}
    </span>
  );
}

export function StatStrip({ children }: { children: ReactNode }) {
  return (
    <div className="glow-card grid grid-cols-2 divide-x divide-y divide-rule rounded-2xl border border-rule bg-chrome lg:grid-cols-4 lg:divide-y-0">
      {children}
    </div>
  );
}

export function Stat({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "default" | "bypassed" | "defended" | "errored" | "brand";
}) {
  const toneClass = {
    default: "text-ink",
    bypassed: "text-signal-soft",
    defended: "text-verdict-soft",
    errored: "text-caution-soft",
    brand: "text-brass",
  }[tone];
  return (
    <div className="relative z-[1] px-4 py-3" title={hint}>
      <div className="font-mono text-2xs tracking-[0.14em] text-ink-3 uppercase">{label}</div>
      <div className={`tnum mt-1.5 text-2xl leading-none font-semibold ${toneClass}`}>{value}</div>
      {hint ? <div className="mt-1.5 text-2xs leading-snug text-ink-3">{hint}</div> : null}
    </div>
  );
}

const TONES: Record<string, string> = {
  bypassed: "border-signal/60 text-signal-soft",
  defended: "border-verdict/60 text-verdict-soft",
  errored: "border-caution/60 text-caution-soft",
  critical: "border-signal/60 text-signal-soft",
  moderate: "border-caution/60 text-caution-soft",
  authorized: "border-verdict/60 text-verdict-soft",
  denied: "border-caution/60 text-caution-soft",
  brass: "border-brass/60 text-brass",
  neutral: "border-rule text-ink-2",
};

export function Tag({ children, tone = "neutral" }: { children: ReactNode; tone?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 border px-1.5 py-0.5 font-mono text-2xs font-medium tracking-[0.1em] uppercase ${
        TONES[tone] ?? TONES.neutral
      }`}
    >
      {children}
    </span>
  );
}

export function Untrusted({ label, value }: { label: string; value: unknown }) {
  const text =
    value === null || value === undefined || String(value).trim() === ""
      ? "(empty)"
      : String(value);
  return (
    <div>
      <div className="mb-1 font-mono text-2xs tracking-[0.14em] text-ink-3 uppercase">{label}</div>
      <pre className="untrusted max-h-56 overflow-auto rounded-lg border border-rule-soft bg-void p-2.5 text-xs leading-relaxed text-ink-2">
        {text}
      </pre>
    </div>
  );
}

export function Note({
  children,
  tone = "brass",
}: {
  children: ReactNode;
  tone?: "brass" | "warn" | "bad";
}) {
  const cls = {
    brass: "border-l-brass",
    warn: "border-l-caution",
    bad: "border-l-signal",
  }[tone];
  return (
    <div
      className={`rounded-r-lg border border-rule border-l-2 bg-chrome px-3.5 py-2.5 text-xs leading-relaxed text-ink-2 ${cls}`}
    >
      {children}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-rule px-4 py-8 text-center font-mono text-2xs tracking-wide text-ink-3">
      {children}
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden bg-chrome-2 ${className}`} aria-hidden="true">
      <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/5 to-transparent [animation:shimmer_1.6s_infinite]" />
    </div>
  );
}

export function LoadingView() {
  return (
    <div className="space-y-4" role="status" aria-live="polite" aria-busy="true">
      <span className="sr-only">Loading records…</span>
      <Skeleton className="h-20 rounded-2xl border border-rule" />
      <Skeleton className="h-64 rounded-2xl border border-rule" />
      <Skeleton className="h-40 rounded-2xl border border-rule" />
    </div>
  );
}

export function ScrollX({ children, label }: { children: ReactNode; label: string }) {
  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={label}>
      {children}
    </div>
  );
}

/** End-of-run payoff shared by every scripted act: the run was scripted for
 *  pacing, but the numbers underneath it are the real logged results. */
export function CompletionCard({
  stats,
  onExit,
}: {
  stats: { value: string; label: string; tone?: "signal" | "verdict" | "brass" }[];
  onExit: () => void;
}) {
  return (
    <Reveal>
      <div className="mt-8 border border-brass/50 bg-chrome p-6">
        <p className="font-mono text-2xs tracking-[0.14em] text-brass uppercase">Simulation complete</p>
        <p className="mt-2 max-w-xl text-sm leading-relaxed text-ink-2">
          This was scripted for pacing — but it re-enacts real, logged results. The actual full run behind it:
        </p>
        <div className="mt-4 flex flex-wrap gap-10">
          {stats.map((s) => (
            <div key={s.label}>
              <div
                className={`tnum text-3xl font-bold ${
                  s.tone === "signal" ? "text-signal-soft" : s.tone === "verdict" ? "text-verdict-soft" : "text-brass"
                }`}
              >
                {s.value}
              </div>
              <div className="mt-1 font-mono text-2xs text-ink-3 uppercase">{s.label}</div>
            </div>
          ))}
        </div>
        <button
          onClick={onExit}
          className="mt-6 inline-flex items-center gap-1.5 border border-brass px-3 py-1.5 font-mono text-2xs font-semibold tracking-[0.14em] text-brass uppercase transition-colors hover:bg-brass hover:text-void"
        >
          See the real dashboard →
        </button>
      </div>
    </Reveal>
  );
}

export function Select({
  label,
  value,
  onChange,
  children,
  className = "",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  children: ReactNode;
  className?: string;
}) {
  return (
    <select
      aria-label={label}
      className={`cursor-pointer border border-rule bg-void px-2.5 py-1.5 font-mono text-xs text-ink-2 transition-colors outline-none hover:border-brass/60 focus:border-brass ${className}`}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      {children}
    </select>
  );
}

export function Th({
  children,
  align = "left",
  title,
}: {
  children: ReactNode;
  align?: "left" | "right";
  title?: string;
}) {
  return (
    <th
      scope="col"
      title={title}
      className={`border-b border-rule px-3 py-2 font-mono text-2xs font-semibold tracking-[0.14em] text-ink-3 uppercase ${
        align === "right" ? "text-right" : "text-left"
      }`}
    >
      {children}
    </th>
  );
}

export function Td({
  children,
  align = "left",
  mono = false,
  className = "",
}: {
  children: ReactNode;
  align?: "left" | "right";
  mono?: boolean;
  className?: string;
}) {
  return (
    <td
      className={`border-b border-rule-soft px-3 py-1.5 text-xs ${
        align === "right" ? "text-right" : ""
      } ${mono ? "tnum" : ""} ${className}`}
    >
      {children}
    </td>
  );
}
