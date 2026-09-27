"""
drive_handler.py — Google Drive integration
Reads the Queue folder, downloads video files, moves to Uploaded,
and updates upload_log.csv so the dashboard can display live data.
"""

import os
import io
import json
import csv
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

SCOPES = [
    "https://www.googleapis.com/auth/drive",
]

# ── Folder names inside your Google Drive root folder ─────────────────────────
QUEUE_FOLDER_NAME    = "Queue"
UPLOADED_FOLDER_NAME = "Uploaded"
FAILED_FOLDER_NAME   = "Failed"
LOG_FILE_NAME        = "upload_log.csv"

LOG_HEADERS = [
    "episode_id", "title", "upload_date", "upload_time",
    "youtube_url", "youtube_status",
    "instagram_url", "instagram_status"
]


class DriveHandler:
    def __init__(self, service_account_file: str):
        creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES
        )
        self.service = build("drive", "v3", credentials=creds)
        self.root_folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]

    # ── Internal: find a subfolder by name ────────────────────────────────────
    def _find_folder(self, name: str, parent_id: str = None) -> str | None:
        parent = parent_id or self.root_folder_id
        q = (f"name='{name}' and mimeType='application/vnd.google-apps.folder' "
             f"and '{parent}' in parents and trashed=false")
        res = self.service.files().list(q=q, fields="files(id,name)").execute()
        files = res.get("files", [])
        return files[0]["id"] if files else None

    # ── Internal: find a file by name in a folder ─────────────────────────────
    def _find_file(self, name: str, parent_id: str) -> str | None:
        q = f"name='{name}' and '{parent_id}' in parents and trashed=false"
        res = self.service.files().list(q=q, fields="files(id,name)").execute()
        files = res.get("files", [])
        return files[0]["id"] if files else None

    # ── Get next episode folder from Queue ────────────────────────────────────
    def get_next_episode(self, force_id: str = None) -> dict | None:
        """
        Looks inside GoogleDrive/VideoAutoUploader/Queue/ for episode folders.
        Each episode folder contains:
          - video.mp4 (or *.mp4)
          - thumbnail.jpg (optional)
          - meta.json  (title, description, tags, ig_caption, etc.)
        Returns a dict with all info, or None if queue is empty.
        """
        queue_id = self._find_folder(QUEUE_FOLDER_NAME)
        if not queue_id:
            print("⚠️  Queue folder not found in Google Drive!")
            return None

        # List all subfolders in Queue (each = one episode)
        q = f"mimeType='application/vnd.google-apps.folder' and '{queue_id}' in parents and trashed=false"
        res = self.service.files().list(
            q=q,
            fields="files(id,name)",
            orderBy="name"          # alphabetical = upload oldest first
        ).execute()
        folders = res.get("files", [])

        if not folders:
            return None

        # If force_id given, find that specific episode folder
        if force_id:
            target = next((f for f in folders if force_id.lower() in f["name"].lower()), None)
            folder = target or folders[0]
        else:
            folder = folders[0]

        folder_id = folder["id"]
        folder_name = folder["name"]
        print(f"📂 Found episode folder: {folder_name}")

        # List files inside this episode folder
        q2 = f"'{folder_id}' in parents and trashed=false"
        res2 = self.service.files().list(q=q2, fields="files(id,name,mimeType)").execute()
        files = res2.get("files", [])

        # Find video, thumbnail, meta
        video_file    = next((f for f in files if f["name"].endswith(".mp4")), None)
        thumb_file    = next((f for f in files if f["name"] in ("thumbnail.jpg", "thumbnail.png")), None)
        meta_file     = next((f for f in files if f["name"] == "meta.json"), None)

        if not video_file:
            print(f"⚠️  No .mp4 found in {folder_name}!")
            return None

        # Read meta.json
        meta = {}
        if meta_file:
            content = self._download_as_bytes(meta_file["id"])
            meta = json.loads(content.decode("utf-8"))

        return {
            "id"               : folder_name,
            "folder_id"        : folder_id,
            "title"            : meta.get("title", folder_name),
            "description"      : meta.get("description", ""),
            "tags"             : meta.get("tags", []),
            "ig_caption"       : meta.get("ig_caption", meta.get("description", "")),
            "category_id"      : meta.get("category_id", "28"),
            "privacy"          : meta.get("privacy", "public"),
            "video_file_id"    : video_file["id"],
            "thumbnail_file_id": thumb_file["id"] if thumb_file else None,
        }

    # ── Download a file by ID to local path ───────────────────────────────────
    def download_file(self, file_id: str, local_name: str) -> str:
        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(local_name, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"   ↓ {int(status.progress() * 100)}%")
        fh.close()
        print(f"   ✅ Downloaded to {local_name}")
        return local_name

    # ── Download file as bytes (for meta.json) ────────────────────────────────
    def _download_as_bytes(self, file_id: str) -> bytes:
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return fh.getvalue()

    # ── Move episode folder to Uploaded/ ─────────────────────────────────────
    def move_to_uploaded(self, folder_id: str):
        queue_id    = self._find_folder(QUEUE_FOLDER_NAME)
        uploaded_id = self._find_folder(UPLOADED_FOLDER_NAME)
        if not uploaded_id:
            # Create Uploaded folder if it doesn't exist
            uploaded_id = self.service.files().create(body={
                "name": UPLOADED_FOLDER_NAME,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [self.root_folder_id]
            }, fields="id").execute()["id"]

        self.service.files().update(
            fileId=folder_id,
            addParents=uploaded_id,
            removeParents=queue_id,
            fields="id, parents"
        ).execute()
        print(f"📁 Moved episode folder to Uploaded/")

    # ── Move episode folder to Failed/ ────────────────────────────────────────
    def move_to_failed(self, folder_id: str):
        queue_id  = self._find_folder(QUEUE_FOLDER_NAME)
        failed_id = self._find_folder(FAILED_FOLDER_NAME)
        if not failed_id:
            failed_id = self.service.files().create(body={
                "name": FAILED_FOLDER_NAME,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [self.root_folder_id]
            }, fields="id").execute()["id"]

        self.service.files().update(
            fileId=folder_id,
            addParents=failed_id,
            removeParents=queue_id,
            fields="id, parents"
        ).execute()
        print(f"📁 Moved episode folder to Failed/")

    # ── Get a public shareable URL for a file ─────────────────────────────────
    def get_public_url(self, file_id: str) -> str:
        """Make file public and return direct download URL (needed for Instagram API)."""
        self.service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"}
        ).execute()
        return f"https://drive.google.com/uc?export=download&id={file_id}"

    # ── Read/write upload_log.csv ─────────────────────────────────────────────
    def read_log(self) -> list[dict]:
        log_id = self._find_file(LOG_FILE_NAME, self.root_folder_id)
        if not log_id:
            return []
        content = self._download_as_bytes(log_id)
        rows = []
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        for row in reader:
            rows.append(row)
        return rows

    def write_log(self, rows: list[dict]):
        """Overwrite upload_log.csv on Drive with updated rows."""
        log_id = self._find_file(LOG_FILE_NAME, self.root_folder_id)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=LOG_HEADERS)
        writer.writeheader()
        writer.writerows(rows)
        csv_bytes = output.getvalue().encode("utf-8")

        from googleapiclient.http import MediaIoBaseUpload
        media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype="text/csv", resumable=False)

        if log_id:
            self.service.files().update(fileId=log_id, media_body=media).execute()
        else:
            self.service.files().create(
                body={"name": LOG_FILE_NAME, "parents": [self.root_folder_id]},
                media_body=media, fields="id"
            ).execute()
            # Make it public so dashboard can read it
            self.get_public_url(self._find_file(LOG_FILE_NAME, self.root_folder_id))

        print(f"📊 upload_log.csv updated on Drive")
