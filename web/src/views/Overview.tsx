import Stepper, { Step } from "../components/Stepper";

/* A guided walkthrough of the whole system, in build order - problem, agent,
 * attack, finding, sentinel, dashboard. Exists for the pitch video: narrating
 * live over six fixed slides beats freehand-scrolling the other tabs. */

function Slide({
  eyebrow,
  title,
  italic,
  lines,
  stat,
}: {
  eyebrow: string;
  title: string;
  italic?: string;
  lines: string[];
  stat?: { value: string; label: string }[];
}) {
  return (
    <div>
      <span className="font-mono text-2xs tracking-[0.2em] text-brass uppercase">{eyebrow}</span>
      <h3 className="mt-2 font-serif text-3xl leading-[1.1] text-ink">
        {title}
        {italic ? <span className="text-ink-2 italic"> {italic}</span> : null}
      </h3>
      <div className="mt-4 space-y-2">
        {lines.map((l, i) => (
          <p key={i} className="text-sm leading-relaxed text-ink-2">
            {l}
          </p>
        ))}
      </div>
      {stat ? (
        <div className="mt-5 flex gap-8 border-t border-rule pt-4">
          {stat.map((s) => (
            <div key={s.label}>
              <div className="tnum text-2xl font-bold text-brass">{s.value}</div>
              <div className="mt-0.5 font-mono text-2xs tracking-[0.14em] text-ink-3 uppercase">
                {s.label}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export interface CompletedActs {
  redteam: boolean;
  drift: boolean;
  mandates: boolean;
}

function CompletionStrip({ completed }: { completed: CompletedActs }) {
  const acts: { key: keyof CompletedActs; label: string }[] = [
    { key: "redteam", label: "Red Team" },
    { key: "drift", label: "Drift" },
    { key: "mandates", label: "Mandates" },
  ];
  const allDone = acts.every((a) => completed[a.key]);

  return (
    <div
      className={`mx-auto mb-8 flex max-w-xl flex-wrap items-center justify-center gap-x-6 gap-y-2 border px-5 py-3 font-mono text-2xs tracking-[0.1em] uppercase ${
        allDone ? "border-verdict/60 bg-verdict/10 text-verdict-soft" : "border-rule bg-chrome text-ink-3"
      }`}
    >
      {allDone ? (
        <span className="font-bold">✓ All three simulations complete</span>
      ) : (
        acts.map((a) => (
          <span key={a.key} className={completed[a.key] ? "text-verdict-soft" : "text-ink-3"}>
            {completed[a.key] ? "✓" : "○"} {a.label}
          </span>
        ))
      )}
    </div>
  );
}

export function Overview({ completedActs }: { completedActs?: CompletedActs }) {
  return (
    <div className="mx-auto max-w-4xl py-6">
      <div className="mb-10 text-center">
        <span className="font-mono text-2xs tracking-[0.2em] text-brass uppercase">
          How Argus works
        </span>
        <h2 className="mt-3 font-serif text-4xl text-ink">Six steps, one audit trail.</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm text-ink-2">
          The same six steps the real Argus build runs — walk through them here, then go run each one
          live under Red Team, Drift, and Mandates.
        </p>
      </div>

      {completedActs ? <CompletionStrip completed={completedActs} /> : null}

      <Stepper backButtonText="Back" nextButtonText="Next">
        <Step>
          <Slide
            eyebrow="01 · The problem"
            title="Agentic commerce agents"
            italic="lie."
            lines={[
              "They hallucinate prices, invent discount codes, and keep answering with stale policy after the ground truth changes.",
              "There's no standard QA layer for that failure mode — most teams find out from a support ticket, not a test.",
            ]}
          />
        </Step>

        <Step>
          <Slide
            eyebrow="02 · The target"
            title="One small commerce agent —"
            italic="everything else attacks it."
            lines={[
              "Gemini 3.5 Flash-Lite, an MCP client against Razorpay's own remote server, real cart/coupon/checkout math computed server-side.",
              "A mandate gate sits in front of every payment link — the model is never trusted to state its own total.",
            ]}
          />
        </Step>

        <Step>
          <Slide
            eyebrow="03 · Pre-deployment"
            title="The red-team harness"
            italic="attacks it first."
            lines={[
              "DeepTeam running the full OWASP_ASI_2026 framework, plus four commerce-specific vulnerabilities this repo wrote: price manipulation, fake discount codes, unauthorized refunds, mandate bypass.",
              "Every attempt is scored and logged with its OWASP ASI category — that's the Red Team tab.",
            ]}
            stat={[{ value: "65", label: "vulnerability types" }]}
          />
        </Step>

        <Step>
          <Slide
            eyebrow="04 · What it caught"
            title="The gate accepted"
            italic="three lies."
            lines={[
              'A claimed prior confirmation, a forged "SYSTEM MESSAGE", a borrowed third-party approval — the keyword gate authorized a real payment on all three.',
              "Fixed with challenge-response: the backend must ask first, quoting the real total, before any answer counts.",
            ]}
            stat={[
              { value: "50%", label: "ASR before" },
              { value: "0%", label: "ASR after" },
            ]}
          />
        </Step>

        <Step>
          <Slide
            eyebrow="05 · Post-deployment"
            title="The drift sentinel"
            italic="watches after."
            lines={[
              "Numeric exact-match on prices, RAGAS Faithfulness on policy text, self-consistency sampling on claims with no ground truth at all.",
              "Every flagged incident gets a cause (stale ground truth vs. fabrication) and a severity — that's the Drift tab.",
            ]}
          />
        </Step>

        <Step>
          <Slide
            eyebrow="06 · This dashboard"
            title="You're looking at"
            italic="the audit trail."
            lines={[
              "No backend — the browser reads Supabase directly on an anon key that can only SELECT, enforced by row-level security.",
              "Every row on every tab drills into the real logged conversation behind it. Findings, Red Team, Drift, Mandates — go look.",
            ]}
          />
        </Step>
      </Stepper>
    </div>
  );
}
