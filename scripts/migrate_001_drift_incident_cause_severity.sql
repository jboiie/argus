-- Migration 001: add drift_cause and severity to drift_incidents.
-- Run once in the Supabase SQL editor, after setup_supabase.sql, before
-- the drift sentinel (build steps 16-20) starts writing rows.
--
-- See DataModel.md's Drift Incident entity for the classification logic
-- and the graceful-degradation behavior rule this enables.

CREATE TYPE drift_cause AS ENUM ('stale_ground_truth', 'fabrication', 'inconsistency');
CREATE TYPE drift_severity AS ENUM ('critical', 'moderate');

ALTER TABLE drift_incidents
    ADD COLUMN drift_cause drift_cause,
    ADD COLUMN severity drift_severity;

-- Both nullable: null when flagged = false/null (nothing to classify),
-- same reasoning as the existing reviewed_at/is_false_positive columns.

CREATE INDEX idx_drift_incidents_severity ON drift_incidents (severity);
