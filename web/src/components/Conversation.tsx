import { useEffect, useState } from "react";
import { fetchSessionTurns } from "../lib/data";
import type { SessionTurn } from "../lib/types";
import { Untrusted } from "./ui";

/** Lazily loads the transcript behind a selected row - the audit trail
 *  Section 4.5 requires. Fetched per-session rather than up front: pulling
 *  every turn for every row would be thousands of rows nobody opens. */
export function Conversation({ sessionId }: { sessionId: string }) {
  const [turns, setTurns] = useState<SessionTurn[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setTurns(null);
    setError(null);
    fetchSessionTurns(sessionId)
      .then((t) => !cancelled && setTurns(t))
      .catch((e) => !cancelled && setError(String(e)));
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  if (error)
    return <p className="mt-4 text-2xs text-caution-soft">Couldn't load transcript: {error}</p>;
  if (turns === null) return <p className="mt-4 text-2xs text-ink-3">Loading transcript…</p>;
  if (turns.length === 0)
    return <p className="mt-4 text-2xs text-ink-3">No conversation turns logged for this session.</p>;

  return (
    <div className="mt-4 border-t border-rule pt-3.5">
      <div className="mb-2 text-2xs font-semibold tracking-[0.08em] text-ink-3 uppercase">
        Conversation transcript
      </div>
      <div className="space-y-2.5">
        {turns.map((t) => (
          <Untrusted key={t.turn_index} label={`turn ${t.turn_index} · ${t.role}`} value={t.content} />
        ))}
      </div>
    </div>
  );
}
