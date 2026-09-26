-- Migration 004: laya_drift_scores - Laya cascade logging (Step 5).
-- Run once in the Supabase SQL editor, after migrate_001-003.
-- NOT YET APPLIED - review before running.
--
-- One row per faithfulness check the drift sampler ran through the Laya
-- cascade (drift/sampler.py, LAYA_CASCADE_ENABLED). A sibling table to
-- drift_incidents, not an ALTER on it - the existing table's shape (one
-- row per check, check_type/question/expected/actual/score/flagged)
-- stays exactly as every other check type already produces it; this adds
-- only what's specific to how the cascade reached that row's verdict.
-- incident_id is the FK back to the drift_incidents row this score
-- belongs to (see telemetry/supabase_client.py::log_drift_incident,
-- which now returns that id for exactly this purpose).

CREATE TABLE laya_drift_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES drift_incidents (incident_id),
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT now(),
    topic TEXT NOT NULL,
    p_faithful DOUBLE PRECISION NOT NULL,       -- Laya's calibrated P(faithful)
    decided_by TEXT NOT NULL CHECK (decided_by IN ('laya', 'ragas')),
    final_verdict TEXT CHECK (final_verdict IN ('faithful', 'unfaithful')),  -- null when errored
    laya_latency_ms DOUBLE PRECISION NOT NULL,
    ragas_latency_ms DOUBLE PRECISION,          -- null unless decided_by = 'ragas'
    errored BOOLEAN NOT NULL DEFAULT false      -- true when the RAGAS escalation call itself errored
);

CREATE INDEX idx_laya_drift_scores_incident ON laya_drift_scores (incident_id);
CREATE INDEX idx_laya_drift_scores_decided_by ON laya_drift_scores (decided_by);

ALTER TABLE laya_drift_scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon read only" ON laya_drift_scores FOR SELECT TO anon USING (true);
