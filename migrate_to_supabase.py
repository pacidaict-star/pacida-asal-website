#!/usr/bin/env python3
"""One-time migration: loads PACIDA's existing assets/interventions.json (236 projects) and
bulk-inserts them into the new Supabase projects/project_locations tables (see
supabase/schema.sql). Run once, locally, after the schema has been created.

Uses the service_role key (bypasses RLS for the bulk insert) — this key must NEVER be committed.
It's read from an environment variable, never written to disk by this script.

Usage:
    SUPABASE_URL="https://xxxx.supabase.co" SUPABASE_SERVICE_ROLE_KEY="..." python migrate_to_supabase.py

status/theme_color/duration/year are intentionally NOT migrated — they're all derived (from
end_date, from theme, from the two dates, from start_date respectively) by the live site and the
projects_live view going forward, not stored. Any project whose old hand-set `status` disagrees
with what the date-derived logic now says is printed at the end as an FYI (these are expected,
desirable corrections — the old data was manually curated and drifted from the actual dates in a
few places), not a migration bug.
"""
import json, os, sys, datetime, urllib.request, urllib.error

SITE = os.path.dirname(os.path.abspath(__file__))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SERVICE_KEY:
    print("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables first.", file=sys.stderr)
    print("(Project Settings -> API in the Supabase dashboard. Use the service_role key here,", file=sys.stderr)
    print(" never the anon key — this script needs to bypass RLS to bulk-insert.)", file=sys.stderr)
    sys.exit(1)


# mirrors build_interventions.py's to_date() (L66-77) — duplicated rather than imported, since
# build_interventions.py re-runs its whole spreadsheet pipeline and overwrites interventions.json
# as a module-level side effect the moment it's imported.
def to_date(v):
    if isinstance(v, str):
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                return datetime.datetime.strptime(v.strip(), fmt).date()
            except ValueError:
                pass
    return None


def api_post(path, body, return_representation=True):
    req = urllib.request.Request(
        SUPABASE_URL + "/rest/v1/" + path,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "apikey": SERVICE_KEY,
            "Authorization": "Bearer " + SERVICE_KEY,
            "Content-Type": "application/json",
            "Prefer": "return=representation" if return_representation else "return=minimal",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
        return json.loads(data) if data else None


def main():
    data = json.load(open(os.path.join(SITE, "assets", "interventions.json"), encoding="utf-8"))
    projects = data["projects"]
    today = datetime.date.today()

    inserted, failed, status_corrections = 0, [], []

    for p in projects:
        start = to_date(p.get("start"))
        end = to_date(p.get("end"))
        if not start:
            failed.append((p.get("id"), p.get("title"), "unparseable start date: %r" % p.get("start")))
            continue

        row = {
            "title": p["title"],
            "donor": p.get("donor") or None,
            "theme": p.get("theme") or "Other",
            "start_date": start.isoformat(),
            "end_date": end.isoformat() if end else None,
            "population_note": p.get("population") or None,
        }

        try:
            created = api_post("projects", row)
        except urllib.error.HTTPError as e:
            failed.append((p.get("id"), p.get("title"), "%s: %s" % (e.code, e.read().decode("utf-8", "replace"))))
            continue

        new_id = created[0]["id"] if isinstance(created, list) else created["id"]

        for loc in p.get("locations", []):
            loc_row = {
                "project_id": new_id,
                "slug": loc["slug"],
                "kind": loc.get("kind") or "site",
                "name": loc.get("name") or loc["slug"],
                "lat": loc["lat"],
                "lon": loc["lon"],
            }
            try:
                api_post("project_locations", loc_row, return_representation=False)
            except urllib.error.HTTPError as e:
                failed.append((p.get("id"), p.get("title"),
                                "location insert failed (%s): %s" % (loc.get("name"), e.read().decode("utf-8", "replace"))))

        inserted += 1

        derived_status = "ongoing" if (end is None or end >= today) else "completed"
        if p.get("status") and p["status"] != derived_status:
            status_corrections.append((p.get("id"), p["title"], p["status"], derived_status))

        if inserted % 25 == 0:
            print("...%d/%d migrated" % (inserted, len(projects)))

    print()
    print("Migrated %d/%d projects." % (inserted, len(projects)))

    if status_corrections:
        print()
        print("%d project(s) will now show a different status than before (derived from dates —" % len(status_corrections))
        print("this is expected/desirable, the old status field was manually set and had drifted):")
        for pid, title, old, new in status_corrections:
            print("  [%s] %-60s %s -> %s" % (pid, title[:60], old, new))

    if failed:
        print()
        print("%d row(s) failed to migrate — review and re-run manually if needed:" % len(failed))
        for pid, title, err in failed:
            print("  [%s] %s: %s" % (pid, title, err))


if __name__ == "__main__":
    main()
