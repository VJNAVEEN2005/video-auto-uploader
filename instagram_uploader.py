"""
instagram_uploader.py — Instagram Graph API Reels uploader
Uses the official Meta Graph API (no browser needed).
Works for Creator and Business accounts.

Flow:
  1. Upload video container (resumable)
  2. Poll until container is ready
  3. Publish the container
"""

import time
import requests


class InstagramUploader:
    BASE_URL = "https://graph.instagram.com/v23.0"

    def __init__(self, access_token: str, account_id: str):
        self.token      = access_token
        self.account_id = account_id

    def upload_reel(
        self,
        video_url: str,
        caption: str,
        cover_url: str = None      # public URL to a JPEG cover image (9:16, <=8MB)
    ) -> dict:
        """
        Upload a Reel to Instagram via Graph API.
        video_url: publicly accessible URL (e.g., Google Drive public link)
        cover_url: optional public URL to the cover image. Must be JPEG,
                   <=8MB, sRGB. 9:16 avoids cropping. Instagram cURLs it,
                   so the Drive file must be shared publicly.
        Returns {success, url, media_id, error}
        """
        try:
            # ── Step 1: Create media container ────────────────────────────────
            print("   📤 Creating Instagram media container...")
            payload = {
                "media_type":  "REELS",
                "video_url":   video_url,
                "caption":     caption[:2200],  # IG max 2200 chars
                "share_to_feed": "true",
                "access_token": self.token
            }
            if cover_url:
                payload["cover_url"] = cover_url
                print(f"   Custom cover: {cover_url}")
            else:
                print("   No cover_url - Instagram picks a frame itself")

            r = requests.post(
                f"{self.BASE_URL}/{self.account_id}/media",
                data=payload,
                timeout=60
            )
            r.raise_for_status()
            container_id = r.json()["id"]
            print(f"   📦 Container created: {container_id}")

            # ── Step 2: Poll until container is ready ─────────────────────────
            print("   ⏳ Waiting for Instagram to process video...")
            for attempt in range(20):  # max ~5 minutes
                time.sleep(15)
                status_r = requests.get(
                    f"{self.BASE_URL}/{container_id}",
                    params={
                        "fields": "status_code,status",
                        "access_token": self.token
                    },
                    timeout=30
                )
                status_r.raise_for_status()
                status_data = status_r.json()
                status_code = status_data.get("status_code", "")
                print(f"   Status ({attempt+1}/20): {status_code}")

                if status_code == "FINISHED":
                    break
                elif status_code == "ERROR":
                    raise RuntimeError(f"Instagram container error: {status_data}")
            else:
                raise TimeoutError("Instagram video processing timed out after 5 minutes")

            # ── Step 3: Publish ────────────────────────────────────────────────
            print("   🚀 Publishing Reel...")
            pub_r = requests.post(
                f"{self.BASE_URL}/{self.account_id}/media_publish",
                data={
                    "creation_id":  container_id,
                    "access_token": self.token
                },
                timeout=30
            )
            pub_r.raise_for_status()
            media_id = pub_r.json()["id"]

            # ── Get permalink ─────────────────────────────────────────────────
            permalink_r = requests.get(
                f"{self.BASE_URL}/{media_id}",
                params={"fields": "permalink", "access_token": self.token},
                timeout=15
            )
            url = permalink_r.json().get("permalink", f"https://www.instagram.com/")
            print(f"   ✅ Instagram Reel posted! {url}")
            return {"success": True, "url": url, "media_id": media_id}

        except Exception as e:
            print(f"   ❌ Instagram upload failed: {e}")
            return {"success": False, "url": "", "error": str(e)}
