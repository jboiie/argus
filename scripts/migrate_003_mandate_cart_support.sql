-- Migration 003: mandates table gains cart support.
-- Run once in the Supabase SQL editor, after migrate_002.
--
-- DataModel.md's own Entity 3 notes anticipated this: "product_id -
-- single product only for v1, becomes a line-items array if the cart
-- stretch goal is reached." That goal was reached - see PROJECT_DESC.md
-- Section 4.1 stretch goal, cart + coupon + multi-step checkout.

ALTER TABLE mandates
    ALTER COLUMN product_id DROP NOT NULL,
    ADD COLUMN line_items JSONB,
    ADD COLUMN coupon_code TEXT;

-- product_id is now deprecated (kept only so old pre-cart rows still
-- read back correctly) - new code always writes line_items instead.
