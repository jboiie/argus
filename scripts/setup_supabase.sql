-- Argus Supabase schema, generated from DataModel.md. Run once in the
-- Supabase SQL editor before any live logging (build step 14).
--
-- Product/Policy are NOT here - they live in catalog.json/policies.json
-- (flat files, no DB FK possible into them - see DataModel.md's
-- "Ground-truth ID stability" convention).
--
-- Security: RLS enabled on every table, anon gets SELECT only. The
-- service_role key bypasses RLS entirely by Supabase's own design, so no
-- explicit INSERT/UPDATE policy is needed for it - just never use
-- service_role outside harness/sentinel backend scripts (see DataModel.md's
-- Security convention).

-- ── Enums (only for genuinely fixed, closed sets - see DataModel.md's
-- Fixed-vocabulary convention. Run.label is deliberately NOT an enum here:
-- its value set grows per-run ("phase_a_baseline", "drift_after_price_change",
-- ...) in a way a DB CHECK can't anticipate; validated in application code
-- instead, same reasoning documented in redteam/scoring.py.)

CREATE TYPE run_type AS ENUM ('redteam', 'drift_sample');
CREATE TYPE mandate_scope AS ENUM ('purchase', 'refund', 'discount_application');
CREATE TYPE mandate_status AS ENUM ('authorized', 'denied');
CREATE TYPE asi_category AS ENUM (
    'ASI_01', 'ASI_02', 'ASI_03', 'ASI_04', 'ASI_05',
    'ASI_06', 'ASI_07', 'ASI_08', 'ASI_09', 'ASI_10'
);
CREATE TYPE attack_outcome AS ENUM ('bypassed', 'defended', 'errored');
CREATE TYPE drift_check_type AS ENUM ('numeric', 'faithfulness', 'self_consistency');
CREATE TYPE ground_truth_type AS ENUM ('product', 'policy');
CREATE TYPE drift_check_status AS ENUM ('completed', 'errored');
CREATE TYPE session_type AS ENUM ('smoke_test', 'drift_sampler', 'attack', 'demo');
CREATE TYPE turn_role AS ENUM ('user', 'agent', 'tool_call', 'tool_result');

-- ── Entity 0: Run ─────────────────────────────────────────────

CREATE TABLE runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type run_type NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    label TEXT NOT NULL,
    notes TEXT
);

CREATE INDEX idx_runs_label ON runs (label);

-- ── Entity 3: Mandate ─────────────────────────────────────────

CREATE TABLE mandates (
    mandate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES runs (run_id),
    session_id UUID NOT NULL,
    scope mandate_scope NOT NULL,
    amount INTEGER NOT NULL,  -- paise, see DataModel.md currency convention
    product_id TEXT NOT NULL,  -- references catalog.json's id, not a DB FK
    authorized_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    user_confirmed BOOLEAN NOT NULL,
    status mandate_status NOT NULL,  -- immutable once set, see DataModel.md
    bypass_confirmed_at TIMESTAMPTZ,
    is_live_demo BOOLEAN NOT NULL DEFAULT false,
    real_call_fired BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX idx_mandates_session ON mandates (session_id);
CREATE INDEX idx_mandates_run ON mandates (run_id);

-- ── Entity 4: Attack Event ────────────────────────────────────

CREATE TABLE attack_events (
    attack_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES runs (run_id),
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT now(),
    asi_category asi_category,  -- nullable: custom vulnerabilities may have
        -- no DeepTeam-native risk_category (see redteam/scoring.py's
        -- CUSTOM_VULNERABILITY_ASI fallback mapping, applied at write time)
    vulnerability TEXT NOT NULL,
    vulnerability_type TEXT NOT NULL,
    attack_method TEXT,  -- nullable: DeepTeam returns None for some attacks
    prompt TEXT,  -- nullable: an early-errored attempt may never have
        -- generated a prompt at all (observed empirically, step 11-12)
    response TEXT,  -- nullable per DataModel.md: outcome=errored means no response
    reason TEXT,  -- nullable per DataModel.md: outcome=errored means no judge ran
    outcome attack_outcome NOT NULL,
    session_id UUID NOT NULL,
    mandate_id UUID REFERENCES mandates (mandate_id)
);

CREATE INDEX idx_attack_events_run ON attack_events (run_id);
CREATE INDEX idx_attack_events_asi ON attack_events (asi_category);
CREATE INDEX idx_attack_events_outcome ON attack_events (outcome);
CREATE INDEX idx_attack_events_session ON attack_events (session_id);

-- ── Entity 5: Drift Incident ──────────────────────────────────

CREATE TABLE drift_incidents (
    incident_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES runs (run_id),
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT now(),
    check_type drift_check_type NOT NULL,
    question TEXT NOT NULL,
    ground_truth_ref TEXT NOT NULL,
    ground_truth_type ground_truth_type NOT NULL,
    expected JSONB,  -- snapshot at check-time, not a live lookup - see DataModel.md
    actual JSONB NOT NULL,
    sampled_responses JSONB,  -- self_consistency rows only
    score DOUBLE PRECISION,
    check_status drift_check_status NOT NULL,
    flagged BOOLEAN,  -- null when check_status = errored, not false
    reviewed_at TIMESTAMPTZ,
    is_false_positive BOOLEAN,
    session_id UUID NOT NULL
);

CREATE INDEX idx_drift_incidents_run ON drift_incidents (run_id);
CREATE INDEX idx_drift_incidents_flagged ON drift_incidents (flagged);

-- ── Entity 6: Session / Conversation Turn ────────────────────

CREATE TABLE session_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    run_id UUID NOT NULL REFERENCES runs (run_id),
    session_type session_type NOT NULL,
    turn_index INTEGER NOT NULL,
    role turn_role NOT NULL,
    content TEXT NOT NULL,
    mandate_id UUID REFERENCES mandates (mandate_id),
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, turn_index)
);

CREATE INDEX idx_session_turns_session ON session_turns (session_id);

-- ── Row Level Security ────────────────────────────────────────

ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE mandates ENABLE ROW LEVEL SECURITY;
ALTER TABLE attack_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE drift_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_turns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon read only" ON runs FOR SELECT TO anon USING (true);
CREATE POLICY "anon read only" ON mandates FOR SELECT TO anon USING (true);
CREATE POLICY "anon read only" ON attack_events FOR SELECT TO anon USING (true);
CREATE POLICY "anon read only" ON drift_incidents FOR SELECT TO anon USING (true);
CREATE POLICY "anon read only" ON session_turns FOR SELECT TO anon USING (true);
