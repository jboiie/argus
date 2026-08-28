export type Outcome = "bypassed" | "defended" | "errored";

export interface Run {
  run_id: string;
  run_type: "redteam" | "drift_sample";
  started_at: string;
  ended_at: string | null;
  label: string;
  notes: string | null;
}

export interface AttackEvent {
  attack_id: string;
  run_id: string;
  timestamp: string;
  asi_category: string | null;
  vulnerability: string;
  vulnerability_type: string;
  attack_method: string | null;
  prompt: string | null;
  response: string | null;
  reason: string | null;
  outcome: Outcome;
  session_id: string;
  mandate_id: string | null;
}

export interface DriftIncident {
  incident_id: string;
  run_id: string;
  timestamp: string;
  check_type: "numeric" | "faithfulness" | "self_consistency";
  question: string;
  ground_truth_ref: string | null;
  ground_truth_type: "product" | "policy" | null;
  expected: unknown;
  actual: unknown;
  sampled_responses: unknown;
  score: number | null;
  check_status: "completed" | "errored";
  /** null when check_status = errored - never false. A stray false would read
   *  as "checked and clean" to a naive count, which is wrong. */
  flagged: boolean | null;
  drift_cause: string | null;
  severity: "critical" | "moderate" | null;
  reviewed_at: string | null;
  is_false_positive: boolean | null;
  session_id: string;
}

export interface Mandate {
  mandate_id: string;
  run_id: string;
  session_id: string;
  scope: string;
  /** paise - Razorpay's native unit. See DataModel.md's currency convention. */
  amount: number;
  line_items: { product_id: string; quantity: number }[] | null;
  coupon_code: string | null;
  product_id: string | null;
  authorized_at: string;
  expires_at: string;
  user_confirmed: boolean;
  status: "authorized" | "denied";
  bypass_confirmed_at: string | null;
  is_live_demo: boolean;
  real_call_fired: boolean;
}

export interface SessionTurn {
  session_id: string;
  run_id: string;
  session_type: string;
  turn_index: number;
  role: string;
  content: string;
  mandate_id: string | null;
  timestamp: string;
}

export interface CategoryASR {
  asi_category: string | null;
  asi_display_name: string | null;
  vulnerability: string;
  vulnerability_type: string;
  attempts: number;
  bypassed: number;
  defended: number;
  errored: number;
  asr_pct: number;
}

export interface FalsePositiveCost {
  total_flagged: number;
  reviewed: number;
  pending_review: number;
  false_positives: number;
  true_positives: number;
  false_positive_rate: number | null;
  review_cost: number;
}
