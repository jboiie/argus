import { useState } from "react";
import type { Mandate } from "../lib/types";
import {
  Empty,
  Note,
  Panel,
  ScrollX,
  Select,
  Stat,
  StatStrip,
  Tag,
  Td,
  Th,
} from "../components/ui";
import { Conversation } from "../components/Conversation";

const rupees = (paise: number) => `₹${(paise / 100).toFixed(2)}`;

export function Mandates({ mandates }: { mandates: Mandate[] }) {
  const [selected, setSelected] = useState<string | null>(null);

  if (mandates.length === 0)
    return (
      <Empty>
        No mandates logged yet — a checkout has to run against the tools-enabled agent
        (agent/reference_agent.py::ask_with_tools)
      </Empty>
    );

  const authorized = mandates.filter((m) => m.status === "authorized").length;
  const denied = mandates.filter((m) => m.status === "denied").length;
  const liveCalls = mandates.filter((m) => m.real_call_fired).length;
  const bypassed = mandates.filter((m) => m.bypass_confirmed_at).length;
  const row = mandates.find((m) => m.mandate_id === selected) ?? mandates[0];

  return (
    <div className="space-y-5">
      <StatStrip>
        <Stat label="Authorized" value={authorized} tone="defended" />
        <Stat label="Denied" value={denied} tone="errored" />
        <Stat
          label="Real Razorpay calls"
          value={liveCalls}
          hint="Test-mode links are capped at 30 per business, so bulk runs are stubbed"
        />
        <Stat
          label="Found bypassable"
          value={bypassed}
          tone={bypassed ? "bypassed" : "default"}
          hint="Recorded separately from status, which is immutable"
        />
      </StatStrip>

      <Note>
        Every mandate creation attempt is logged, authorized or denied, live or stubbed — Track 01's
        <em> "every money action explainable, bounded and gated"</em> bar. This isn't just about
        whether a link gets paid: the same check also gates refunds, and an unauthorized
        "authorized" row is a false record even if nobody ever pays it. The amount itself is
        computed server-side from the cart against real catalog prices; the model never states a
        number that reaches Razorpay.
      </Note>

      {bypassed > 0 ? (
        <Note tone="bad">
          {bypassed} mandate(s) were later confirmed bypassable by an attack. <code>status</code> is
          deliberately left untouched — the original decision stays an immutable record and the
          finding is recorded alongside it.
        </Note>
      ) : null}

      <Panel title="Mandate log">
        <ScrollX label="Mandate log">
          <table className="w-full min-w-[820px] border-collapse">
            <caption className="sr-only">Every mandate creation attempt, authorized or denied</caption>
            <thead>
              <tr>
                <Th>Authorized at</Th>
                <Th>Status</Th>
                <Th>Scope</Th>
                <Th align="right">Amount</Th>
                <Th>Coupon</Th>
                <Th>Confirmed</Th>
                <Th>Call</Th>
                <Th>Bypassed</Th>
              </tr>
            </thead>
            <tbody>
              {mandates.map((m) => (
                <tr key={m.mandate_id} className="transition-colors duration-150 hover:bg-chrome-2">
                  <Td mono className="whitespace-nowrap text-ink-3">
                    {m.authorized_at.slice(0, 16).replace("T", " ")}
                  </Td>
                  <Td><Tag tone={m.status}>{m.status}</Tag></Td>
                  <Td className="text-ink-3">{m.scope}</Td>
                  <Td align="right" mono className="text-ink">{rupees(m.amount)}</Td>
                  <Td mono className="text-ink-3">{m.coupon_code ?? "—"}</Td>
                  <Td className={m.user_confirmed ? "text-verdict-soft" : "text-ink-3"}>
                    {m.user_confirmed ? "yes" : "no"}
                  </Td>
                  <Td className="text-ink-3">{m.real_call_fired ? "live" : "stubbed"}</Td>
                  <Td>
                    {m.bypass_confirmed_at ? (
                      <Tag tone="bypassed">yes</Tag>
                    ) : (
                      <span className="text-ink-3">—</span>
                    )}
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollX>
      </Panel>

      <Panel
        title="Audit trail"
        right={
          <Select
            label="Select a mandate to inspect"
            className="max-w-md min-w-64"
            value={row?.mandate_id ?? ""}
            onChange={setSelected}
          >
            {mandates.map((m) => (
              <option key={m.mandate_id} value={m.mandate_id}>
                {m.status.toUpperCase()} · {rupees(m.amount)} ·{" "}
                {m.authorized_at.slice(0, 16).replace("T", " ")}
              </option>
            ))}
          </Select>
        }
      >
        {row ? (
          <>
            <div className="mb-3.5 flex flex-wrap items-center justify-between gap-2 border-b border-rule pb-3">
              <div>
                <div className="tnum text-sm font-semibold text-ink">
                  {rupees(row.amount)} · {row.scope}
                </div>
                <div className="tnum mt-1 text-2xs text-ink-3">
                  authorized {row.authorized_at.slice(0, 19).replace("T", " ")} · expires{" "}
                  {row.expires_at.slice(0, 19).replace("T", " ")}
                </div>
              </div>
              <Tag tone={row.status}>{row.status}</Tag>
            </div>

            <div className="grid gap-3 lg:grid-cols-2">
              <div>
                <div className="mb-1 text-2xs font-medium tracking-[0.08em] text-ink-3 uppercase">
                  Line items · server-computed from the cart
                </div>
                <pre className="untrusted overflow-auto border border-rule-soft bg-void p-2.5 text-xs text-ink-2">
                  {JSON.stringify(row.line_items ?? [], null, 2)}
                </pre>
              </div>
              <div>
                <div className="mb-1 text-2xs font-medium tracking-[0.08em] text-ink-3 uppercase">
                  Authorization
                </div>
                <dl className="tnum space-y-1 border border-rule-soft bg-void p-2.5 text-xs text-ink-2">
                  <div className="flex justify-between gap-4">
                    <dt className="text-ink-3">coupon</dt>
                    <dd>{row.coupon_code ?? "(none)"}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-ink-3">user_confirmed</dt>
                    <dd>{String(row.user_confirmed)}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-ink-3">is_live_demo</dt>
                    <dd>{String(row.is_live_demo)}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-ink-3">real_call_fired</dt>
                    <dd>{String(row.real_call_fired)}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-ink-3">bypass_confirmed_at</dt>
                    <dd>{row.bypass_confirmed_at ?? "never"}</dd>
                  </div>
                </dl>
              </div>
            </div>

            <Conversation sessionId={row.session_id} />
          </>
        ) : null}
      </Panel>
    </div>
  );
}
