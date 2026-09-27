"""
logger.py — Appends upload results to upload_log.csv on Google Drive.
The dashboard reads this CSV to show live upload history.
"""

from datetime import datetime, timezone, timedelta


IST = timezone(timedelta(hours=5, minutes=30))


class UploadLogger:
    def __init__(self, drive_handler):
        self.drive = drive_handler

    def log(
        self,
        episode_id: str,
        title: str,
        yt_url: str,
        yt_status: str,
        ig_url: str,
        ig_status: str
    ):
        """Append one row to upload_log.csv on Drive."""
        now = datetime.now(IST)
        new_row = {
            "episode_id":       episode_id,
            "title":            title,
            "upload_date":      now.strftime("%Y-%m-%d"),
            "upload_time":      now.strftime("%I:%M %p IST"),
            "youtube_url":      yt_url,
            "youtube_status":   yt_status,
            "instagram_url":    ig_url,
            "instagram_status": ig_status,
        }

        # Read existing rows, append new one, write back
        existing = self.drive.read_log()
        existing.append(new_row)
        self.drive.write_log(existing)
        print(f"   ✅ Logged: {title}")
