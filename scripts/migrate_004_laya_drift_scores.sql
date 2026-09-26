-- Migration 004: laya_drift_scores - Laya cascade logging (Step 5).
-- Run once in the Supabase SQL editor, after migrate_001-003.
-- NOT YET APPLIED - review before running.
--
-- One row per faithfulness check the drift sampler ran through the Laya
-- cascade (drift/sampler.py, LAYA_CASCADE_ENABLED) - EVERY such check,
-- not only ones that end up flagged. Confirmed directly from the code:
-- drift/sampler.py::run_and_log calls log_drift_incident for every row
-- in run_session's results unconditionally (no `if r.flagged` guard
-- anywhere in that loop), so incident_id already exists for every
-- cascade check by the time log_laya_drift_score runs, and this table's
-- row count is a correct 1:1 with cascade checks, not a subset of them.
-- Keying on incident_id (NOT NULL, not nullable) is therefore correct -
-- switching to run_id + a separate sample id was considered and is not
-- needed.
--
-- A sibling table to drift_incidents, not an ALTER on it - the existing
-- table's shape (one row per check, check_type/question/expected/actual/
-- score/flagged) stays exactly as every other check type already
-- produces it; this adds only what's specific to how the cascade reached
-- that row's verdict.

CREATE TABLE laya_drift_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES drift_incidents (incident_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    topic TEXT NOT NULL,
    p_faithful DOUBLE PRECISION NOT NULL,       -- Laya's calibrated P(faithful)
    decided_by TEXT NOT NULL CHECK (decided_by IN ('laya', 'ragas')),
    final_verdict TEXT CHECK (final_verdict IN ('faithful', 'unfaithful')),  -- null when errored
    laya_latency_ms DOUBLE PRECISION NOT NULL,
    ragas_latency_ms DOUBLE PRECISION,          -- null unless decided_by = 'ragas'
    errored BOOLEAN NOT NULL DEFAULT false,     -- true when the RAGAS escalation call itself errored
    threshold DOUBLE PRECISION NOT NULL,        -- the t this check was decided against
    operating_point TEXT NOT NULL CHECK (operating_point IN ('accuracy', 'cost')),
    laya_checkpoint TEXT NOT NULL               -- e.g. 'convaiinnovations/laya:typed-decisions'
);

CREATE INDEX idx_laya_drift_scores_incident ON laya_drift_scores (incident_id);
CREATE INDEX idx_laya_drift_scores_decided_by ON laya_drift_scores (decided_by);
CREATE INDEX idx_laya_drift_scores_operating_point ON laya_drift_scores (operating_point);

ALTER TABLE laya_drift_scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon read only" ON laya_drift_scores FOR SELECT TO anon USING (true);
