import { useState } from "react";
import type { Mandate } from "../lib/types";
import { Badge, Empty, Metric, Note, Panel, SectionTitle } from "../components/ui";
import { Conversation } from "../components/Conversation";

const rupees = (paise: number) => `Rs.${(paise / 100).toFixed(2)}`;

export function Mandates({ mandates }: { mandates: Mandate[] }) {
  const [selected, setSelected] = useState<string | null>(null);

  if (mandates.length === 0)
    return (
      <Empty>
        No mandates logged yet — a checkout has to run against the tools-enabled agent
        (<code>agent/reference_agent.py::ask_with_tools</code>).
      </Empty>
    );

  const authorized = mandates.filter((m) => m.status === "authorized").length;
  const denied = mandates.filter((m) => m.status === "denied").length;
  const liveCalls = mandates.filter((m) => m.real_call_fired).length;
  const bypassed = mandates.filter((m) => m.bypass_confirmed_at).length;
  const row = mandates.find((m) => m.mandate_id === selected) ?? mandates[0];

  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Authorized" value={authorized} tone="defended" />
        <Metric label="Denied" value={denied} tone="errored" />
        <Metric label="Real Razorpay calls" value={liveCalls} hint="Test-mode links are capped at 30 per business, so bulk runs are stubbed" />
        <Metric label="Later found bypassable" value={bypassed} tone={bypassed ? "bypassed" : "default"} hint="Recorded separately from status, which is immutable" />
      </div>

      <Note>
        Every mandate creation attempt is logged, authorized or denied, live or stubbed — Track 01's
        <em> "every money action explainable, bounded and gated"</em> bar. The amount is computed
        server-side from the cart against real catalog prices; the model never states a number that
        reaches Razorpay.
      </Note>

      {bypassed > 0 ? (
        <Note tone="bad">
          {bypassed} mandate(s) were later confirmed bypassable by an attack.{" "}
          <code>status</code> is deliberately left untouched — the original decision stays an
          immutable record, and the finding is recorded alongside it.
        </Note>
      ) : null}

      <Panel>
        <SectionTitle>Mandate log</SectionTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-edge text-left text-[11px] uppercase tracking-wider text-ink-dim">
                <th className="py-2 pr-3 font-medium">Authorized at</th>
                <th className="py-2 pr-3 font-medium">Status</th>
                <th className="py-2 pr-3 font-medium">Scope</th>
                <th className="py-2 pr-3 text-right font-medium">Amount</th>
                <th className="py-2 pr-3 font-medium">Coupon</th>
                <th className="py-2 pr-3 font-medium">Confirmed</th>
                <th className="py-2 pr-3 font-medium">Call fired</th>
                <th className="py-2 font-medium">Bypassed</th>
              </tr>
            </thead>
            <tbody>
              {mandates.map((m) => (
                <tr key={m.mandate_id} className="border-b border-edge/40 hover:bg-panel-2/60">
                  <td className="py-2 pr-3 whitespace-nowrap text-ink-dim">
                    {m.authorized_at.slice(0, 16).replace("T", " ")}
                  </td>
                  <td className="py-2 pr-3"><Badge tone={m.status}>{m.status}</Badge></td>
                  <td className="py-2 pr-3 text-ink-dim">{m.scope}</td>
                  <td className="py-2 pr-3 text-right tabular-nums">{rupees(m.amount)}</td>
                  <td className="py-2 pr-3 text-ink-dim">{m.coupon_code ?? "—"}</td>
                  <td className="py-2 pr-3">{m.user_confirmed ? "yes" : "no"}</td>
                  <td className="py-2 pr-3">{m.real_call_fired ? "yes" : "stubbed"}</td>
                  <td className="py-2">
                    {m.bypass_confirmed_at ? <Badge tone="bypassed">yes</Badge> : <span className="text-ink-dim">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel>
        <SectionTitle>Audit trail</SectionTitle>
        <select
          className="w-full rounded-lg border border-edge bg-ground px-3 py-2 text-sm text-ink outline-none focus:border-accent"
          value={row?.mandate_id ?? ""}
          onChange={(e) => setSelected(e.target.value)}
        >
          {mandates.map((m) => (
            <option key={m.mandate_id} value={m.mandate_id}>
              {m.status.toUpperCase()} · {rupees(m.amount)} ·{" "}
              {m.authorized_at.slice(0, 16).replace("T", " ")}
            </option>
          ))}
        </select>

        {row ? (
          <div className="mt-4 rounded-lg border border-edge bg-ground/40 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="font-semibold text-ink">
                  {rupees(row.amount)} · scope: {row.scope}
                </div>
                <div className="text-xs text-ink-dim">
                  authorized {row.authorized_at.slice(0, 19).replace("T", " ")} · expires{" "}
                  {row.expires_at.slice(0, 19).replace("T", " ")}
                </div>
              </div>
              <Badge tone={row.status}>{row.status}</Badge>
            </div>

            <div className="mt-4">
              <div className="mb-1 text-[11px] font-medium uppercase tracking-wider text-ink-dim">
                Line items — server-computed from the cart, not model-supplied
              </div>
              <pre className="untrusted overflow-auto rounded-lg border border-edge bg-ground/80 p-3 text-[13px] text-ink/90">
                {JSON.stringify(row.line_items ?? [], null, 2)}
              </pre>
            </div>

            <p className="mt-3 text-xs text-ink-dim">
              Coupon: {row.coupon_code ?? "(none)"} · user_confirmed: {String(row.user_confirmed)} ·
              bypass_confirmed_at: {row.bypass_confirmed_at ?? "(never — not bypassed)"}
            </p>

            <Conversation sessionId={row.session_id} />
          </div>
        ) : null}
      </Panel>
    </div>
  );
}
