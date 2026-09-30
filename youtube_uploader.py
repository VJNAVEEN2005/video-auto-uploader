"""
youtube_uploader.py — YouTube Data API v3 uploader
Uses official Google API (no browser needed).
Uploads video, sets thumbnail, title, description, tags, visibility.
"""

import os
import json
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

YOUTUBE_CATEGORIES = {
    "Science & Tech": "28",
    "Entertainment":  "24",
    "Education":      "27",
    "Film & Animation": "1",
    "Gaming":         "20",
}


class YouTubeUploader:
    def __init__(self, token_file: str):
        """
        token_file: path to youtube_token.json
        (generated once by running: python auto-uploader/get_yt_token.py)
        """
        self.token_file = token_file
        self.service = self._build_service()

    def _build_service(self):
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, "r") as f:
                token_data = json.load(f)
            creds = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.environ["YOUTUBE_CLIENT_ID"],
                client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
                scopes=SCOPES
            )
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed token
                with open(self.token_file, "w") as f:
                    json.dump({
                        "token": creds.token,
                        "refresh_token": creds.refresh_token
                    }, f)
            else:
                raise RuntimeError(
                    "YouTube token missing or invalid. "
                    "Run: python auto-uploader/get_yt_token.py  on your PC first!"
                )
        return build("youtube", "v3", credentials=creds)

    def upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list = None,
        thumbnail_path: str = None,
        category_id: str = "28",
        privacy: str = "public"
    ) -> dict:
        """Upload a video to YouTube. Returns {success, url, video_id, error}."""
        try:
            body = {
                "snippet": {
                    "title":       title[:100],  # YouTube max 100 chars
                    "description": description[:5000],
                    "tags":        tags or [],
                    "categoryId":  category_id,
                },
                "status": {
                    "privacyStatus":           privacy.lower(),
                    "selfDeclaredMadeForKids": False,
                }
            }

            media = MediaFileUpload(
                video_path,
                mimetype="video/mp4",
                resumable=True,
                chunksize=10 * 1024 * 1024  # 10 MB chunks
            )

            print("   📤 Starting YouTube upload...")
            request = self.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    pct = int(status.resumable_progress / status.total_size * 100)
                    print(f"   ↑ {pct}% uploaded to YouTube")

            video_id = response["id"]
            url = f"https://www.youtube.com/shorts/{video_id}"
            print(f"   ✅ YouTube upload complete! {url}")

            # Upload thumbnail with ingestion delay and retry logic
            if thumbnail_path and os.path.exists(thumbnail_path):
                # Verify file size (YouTube max is 2MB)
                thumb_size_mb = os.path.getsize(thumbnail_path) / (1024 * 1024)
                if thumb_size_mb > 2.0:
                    print(f"   ⚠️  Warning: Thumbnail file size ({thumb_size_mb:.2f}MB) exceeds YouTube 2MB limit!")
                
                mime = "image/png" if thumbnail_path.lower().endswith(".png") else "image/jpeg"
                print(f"   🖼️  Waiting 6s for YouTube ingestion before setting thumbnail ({thumb_size_mb:.2f}MB)...")
                time.sleep(6)

                thumb_uploaded = False
                for attempt in range(1, 4):
                    try:
                        self.service.thumbnails().set(
                            videoId=video_id,
                            media_body=MediaFileUpload(thumbnail_path, mimetype=mime, resumable=True)
                        ).execute()
                        print("   ✅ Thumbnail uploaded successfully.")
                        thumb_uploaded = True
                        break
                    except Exception as e:
                        err_str = str(e)
                        if "403" in err_str or "uploadForbidden" in err_str:
                            print(f"   ⚠️  Thumbnail 403 Forbidden: Channel lacks Phone Verification / Intermediate features in YouTube Studio, or lacks full OAuth scope.")
                            break
                        print(f"   ⚠️  Thumbnail upload attempt {attempt}/3 note: {e}")
                        if attempt < 3:
                            time.sleep(5 * attempt)

            return {"success": True, "url": url, "video_id": video_id}

        except Exception as e:
            print(f"   ❌ YouTube upload failed: {e}")
            return {"success": False, "url": "", "error": str(e)}
