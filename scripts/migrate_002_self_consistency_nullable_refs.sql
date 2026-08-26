-- Migration 002: relax ground_truth_ref/ground_truth_type to nullable.
-- Run once in the Supabase SQL editor, after migrate_001.
--
-- self_consistency rows (build step 17) check claims NOT covered by
-- ground truth - there's no real Product/Policy id for them to reference,
-- same reasoning DataModel.md already applies to `expected` being null
-- for these rows. Originally both columns were NOT NULL; that assumption
-- only held for numeric/faithfulness checks.

ALTER TABLE drift_incidents
    ALTER COLUMN ground_truth_ref DROP NOT NULL,
    ALTER COLUMN ground_truth_type DROP NOT NULL;
