"""
main.py — Mr.Quasar Auto Uploader
Entry point: picks next video from Google Drive, uploads to YouTube + Instagram,
logs the result, and sends Telegram notification.
"""

import os
import sys
from drive_handler import DriveHandler
from youtube_uploader import YouTubeUploader
from instagram_uploader import InstagramUploader
from telegram_notifier import TelegramNotifier
from logger import UploadLogger

def main():
    print("=" * 60)
    print("🚀 MR.QUASAR AUTO UPLOADER STARTING")
    print("=" * 60)

    # ── Init all services ──────────────────────────────────────────
    if not os.environ.get("DRIVE_TOKEN_JSON"):
        print("❌ DRIVE_TOKEN_JSON secret is not set — cannot access Google Drive.")
        print("   Add it under: Settings → Secrets and variables → Actions")
        sys.exit(1)

    drive    = DriveHandler()
    yt       = YouTubeUploader(token_file="youtube_token.json")
    ig       = InstagramUploader(
                    access_token=os.environ["INSTAGRAM_ACCESS_TOKEN"],
                    account_id=os.environ["INSTAGRAM_ACCOUNT_ID"]
               )
    telegram = TelegramNotifier(
                    bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
                    chat_id=os.environ["TELEGRAM_CHAT_ID"]
               )
    logger   = UploadLogger(drive)

    # ── Pick next video ────────────────────────────────────────────
    force_ep = os.environ.get("FORCE_EPISODE", "").strip()
    episode  = drive.get_next_episode(force_id=force_ep if force_ep else None)

    if not episode:
        msg = "📭 No videos in Queue folder on Google Drive. Nothing to upload today."
        print(msg)
        telegram.send(f"ℹ️ *Mr.Quasar Auto Uploader*\n{msg}")
        sys.exit(0)

    print(f"\n📹 Uploading: {episode['title']}")
    print(f"   Video file ID : {episode['video_file_id']}")
    print(f"   Thumbnail ID  : {episode.get('thumbnail_file_id', 'None')}")

    # ── Download files locally ─────────────────────────────────────
    print("\n[1/4] Downloading video from Drive...")
    video_path = drive.download_file(episode["video_file_id"], "tmp_video.mp4")

    thumbnail_path = None
    if episode.get("thumbnail_file_id"):
        print("[1/4] Downloading thumbnail from Drive...")
        thumbnail_path = drive.download_file(episode["thumbnail_file_id"], "tmp_thumb.jpg")

    # ── Upload to YouTube ─────────────────────────────────────────
    print("\n[2/4] Uploading to YouTube...")
    yt_result = yt.upload(
        video_path=video_path,
        title=episode["title"],
        description=episode["description"],
        tags=episode.get("tags", []),
        thumbnail_path=thumbnail_path,
        category_id=episode.get("category_id", "28"),   # 28 = Science & Tech
        privacy=episode.get("privacy", "public")
    )

    yt_url   = yt_result.get("url", "")
    yt_ok    = yt_result.get("success", False)
    yt_error = yt_result.get("error", "")

    # ── Upload to Instagram ───────────────────────────────────────
    print("\n[3/4] Posting to Instagram Reels...")
    # Instagram needs a PUBLIC video URL — we use the YouTube URL or a Drive direct link
    ig_result = ig.upload_reel(
        video_url=drive.get_public_url(episode["video_file_id"]),
        caption=episode.get("ig_caption", episode["description"]),
        thumbnail_path=thumbnail_path
    )

    ig_url   = ig_result.get("url", "")
    ig_ok    = ig_result.get("success", False)
    ig_error = ig_result.get("error", "")

    # ── Log results ────────────────────────────────────────────────
    print("\n[4/4] Logging results...")
    logger.log(
        episode_id=episode["id"],
        title=episode["title"],
        yt_url=yt_url,
        yt_status="✅ Uploaded" if yt_ok else f"❌ Failed: {yt_error}",
        ig_url=ig_url,
        ig_status="✅ Posted" if ig_ok else f"❌ Failed: {ig_error}",
    )

    # Move video out of Queue only when it actually published. A failed episode
    # goes to Failed/ so it stays visible on the dashboard and can be retried.
    if yt_ok and ig_ok:
        drive.move_to_uploaded(episode["folder_id"])
    else:
        drive.move_to_failed(episode["folder_id"])

    # ── Telegram notification ─────────────────────────────────────
    status_icon = "✅" if (yt_ok and ig_ok) else "⚠️"
    message = (
        f"{status_icon} *Mr.Quasar Auto Uploader*\n\n"
        f"📹 *{episode['title']}*\n\n"
        f"{'✅' if yt_ok else '❌'} YouTube: {yt_url if yt_ok else yt_error}\n"
        f"{'✅' if ig_ok else '❌'} Instagram: {ig_url if ig_ok else ig_error}\n\n"
        f"🕐 Uploaded at 7:30 PM IST"
    )
    telegram.send(message)

    # ── Cleanup temp files ─────────────────────────────────────────
    for f in ["tmp_video.mp4", "tmp_thumb.jpg"]:
        if os.path.exists(f):
            os.remove(f)

    print("\n" + "=" * 60)
    print(f"{status_icon} DONE! YT: {yt_ok} | IG: {ig_ok}")
    print("=" * 60)
    sys.exit(0 if (yt_ok and ig_ok) else 1)


if __name__ == "__main__":
    main()
