import { createClient } from "@supabase/supabase-js";

/**
 * Browser-side Supabase client.
 *
 * Shipping the anon key in a client bundle is deliberate and safe HERE, and
 * only because of how the database is configured: RLS is enabled on every
 * table and anon holds a SELECT-only policy, so the worst a reader can do is
 * read data that is already published on a public dashboard. That is the
 * design DataModel.md's Security convention describes, and it is what makes
 * a backend-free dashboard possible at all.
 *
 * SUPABASE_SERVICE_ROLE_KEY must never appear in this directory. It bypasses
 * RLS entirely and belongs only to the harness/sentinel backend scripts.
 */
const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

export const isConfigured = Boolean(url && anonKey);

export const supabase = isConfigured
  ? createClient(url as string, anonKey as string)
  : null;
