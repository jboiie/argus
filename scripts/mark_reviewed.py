"""One-off review CLI - marks drift_incidents rows reviewed. service_role
key only, never exposed to the dashboard's anon-key path (DataModel.md's
Security convention).

Needed because agent/drift_guard.py's graceful-degradation gate blocks a
ground_truth_ref until its critical incident is reviewed - without this,
accumulated test/demo noise blocks that item forever, and there's no
write path from the (deliberately read-only) public dashboard to clear it.

Usage:
  python scripts/mark_reviewed.py <incident_id> [<incident_id> ...] [--false-positive]
  python scripts/mark_reviewed.py --list-unresolved-critical
"""

import argparse

from telemetry.supabase_client import get_client, mark_drift_incident_reviewed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("incident_ids", nargs="*")
    parser.add_argument("--false-positive", action="store_true")
    parser.add_argument("--list-unresolved-critical", action="store_true")
    args = parser.parse_args()

    client = get_client()

    if args.list_unresolved_critical:
        resp = (
            client.table("drift_incidents")
            .select("incident_id,ground_truth_ref,check_type,timestamp")
            .eq("severity", "critical")
            .is_("reviewed_at", "null")
            .execute()
        )
        for row in resp.data:
            print(row)
        return

    if not args.incident_ids:
        print("No incident_ids given (pass IDs, or --list-unresolved-critical to see what's blocking).")
        return

    for incident_id in args.incident_ids:
        mark_drift_incident_reviewed(client, incident_id, is_false_positive=args.false_positive)
        print(f"reviewed: {incident_id} (false_positive={args.false_positive})")


if __name__ == "__main__":
    main()
