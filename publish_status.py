"""
publish_status.py — writes docs/status.json

The dashboard is a static GitHub Pages site with no access to Google Drive, so
this script snapshots what Drive looks like after every workflow run and commits
the result to the repo. The page just fetches that file.

Run:  python publish_status.py
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

from drive_handler import DriveHandler, UPLOADED_FOLDER_NAME, FAILED_FOLDER_NAME, QUEUE_FOLDER_NAME

IST = timezone(timedelta(hours=5, minutes=30))
OUT_PATH = os.path.join("docs", "status.json")


def day_streak(dates: list[str]) -> int:
    """Consecutive days ending today (or yesterday) that have an upload."""
    if not dates:
        return 0
    have = {datetime.strptime(d, "%Y-%m-%d").date() for d in dates}
    today = datetime.now(IST).date()
    # Allow the streak to start yesterday — today's run may not have happened yet.
    cursor = today if today in have else today - timedelta(days=1)
    if cursor not in have:
        return 0
    streak = 0
    while cursor in have:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def main():
    now = datetime.now(IST)
    drive = DriveHandler()

    queue    = drive.scan_folder(QUEUE_FOLDER_NAME)
    uploaded = drive.scan_folder(UPLOADED_FOLDER_NAME)
    failed   = drive.scan_folder(FAILED_FOLDER_NAME)
    history  = drive.read_log()

    # "Ready" = has both the video and the metadata the uploader needs.
    for ep in queue:
        ep["ready"] = ep["has_video"] and ep["has_meta"]

    last_run_url = os.environ.get("RUN_URL", "").strip()
    last_run     = os.environ.get("RUN_OUTCOME", "").strip().lower()

    status = {
        "generated_at":     now.isoformat(),
        "generated_at_ist": now.strftime("%d %b %Y, %I:%M %p IST"),
        "last_run": {
            "outcome": last_run,
            "url":     last_run_url,
            "at":      now.isoformat() if last_run else None,
        },
        "queue":    queue,
        "uploaded": uploaded,
        "failed":   failed,
        "history":  history,
        "stats": {
            "pending":        len(queue),
            "ready":          sum(1 for e in queue if e["ready"]),
            "blocked":        sum(1 for e in queue if not e["ready"]),
            "total_uploaded": len(uploaded),
            "failed":         len(failed),
            "streak":         day_streak([r.get("upload_date", "") for r in history]),
        },
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

    s = status["stats"]
    print(f"📊 status.json written to {OUT_PATH}")
    print(f"   pending={s['pending']} (ready={s['ready']}, blocked={s['blocked']}) "
          f"uploaded={s['total_uploaded']} failed={s['failed']} streak={s['streak']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never fail the upload job over a dashboard snapshot.
        # ASCII only — this handler must not itself blow up on a cp1252 console.
        print(f"[warn] Could not publish status.json: {type(exc).__name__}: {exc}")
        sys.exit(0)
