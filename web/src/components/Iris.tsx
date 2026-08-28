/**
 * Argus's eye, as a watermark.
 *
 * Concentric broken arcs rather than a literal eyeball: it reads as an
 * aperture / iris diaphragm, which is the right register for a monitoring
 * tool, and the gaps let it sit behind text without fighting it. Purely
 * atmospheric — aria-hidden, no information encoded here.
 */
export function Iris({ className = "" }: { className?: string }) {
  const rings = [
    { r: 132, dash: "6 22", w: 1 },
    { r: 108, dash: "40 26", w: 1.25 },
    { r: 86, dash: "3 14", w: 1 },
    { r: 62, dash: "70 40", w: 1.5 },
    { r: 40, dash: "2 10", w: 1 },
  ];
  return (
    <svg
      viewBox="0 0 320 320"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <radialGradient id="iris-core" cx="50%" cy="50%">
          <stop offset="0%" stopColor="var(--color-brass)" stopOpacity="0.16" />
          <stop offset="70%" stopColor="var(--color-brass)" stopOpacity="0.03" />
          <stop offset="100%" stopColor="var(--color-brass)" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="160" cy="160" r="150" fill="url(#iris-core)" />
      {rings.map((ring) => (
        <circle
          key={ring.r}
          cx="160"
          cy="160"
          r={ring.r}
          fill="none"
          stroke="var(--color-brass)"
          strokeWidth={ring.w}
          strokeDasharray={ring.dash}
          strokeLinecap="round"
          opacity="0.3"
        />
      ))}
      {/* Pupil — the one solid mark, so the eye actually reads as an eye. */}
      <circle cx="160" cy="160" r="16" fill="var(--color-brass)" opacity="0.14" />
      <circle cx="160" cy="160" r="7" fill="var(--color-void)" opacity="0.6" />
    </svg>
  );
}
