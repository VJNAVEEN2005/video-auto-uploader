# 🚀 Mr.Quasar Auto Uploader — Full Setup Guide

> **Uploads daily at 7:30 PM IST** to YouTube Shorts + Instagram Reels  
> Runs on GitHub Actions — works even when your PC is off  
> Dashboard live at: `https://VJNAVEEN2005.github.io/video-auto-uploader/`

---

## 📁 Google Drive Folder Structure

Create this structure in your Google Drive:

```
📁 VideoAutoUploader/           ← This is your ROOT folder
├── 📁 Queue/                   ← Drop videos here to upload
│   ├── 📁 01_My_Video/
│   │   ├── video.mp4           ← Your vertical short video
│   │   ├── thumbnail.jpg       ← Thumbnail image
│   │   └── meta.json           ← Title, description, tags (copy TEMPLATE_meta.json)
│   └── 📁 02_Next_Video/
│       ├── video.mp4
│       ├── thumbnail.jpg
│       └── meta.json
├── 📁 Uploaded/                ← Auto-moved here after upload (don't touch)
├── 📁 Failed/                  ← Auto-moved here if upload fails
└── upload_log.csv              ← Auto-created, dashboard reads this
```

---

## 🔑 Step 1 — Google Cloud Setup (Service Account)

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable these APIs:
   - **Google Drive API**
   - **YouTube Data API v3**
4. Go to **APIs & Services → Credentials**
5. Click **Create Credentials → Service Account**
   - Name: `video-uploader`
   - Role: Editor
6. Click the service account → **Keys tab → Add Key → JSON**
7. Download the JSON file — this is your `GOOGLE_SERVICE_ACCOUNT_JSON`

> ⚠️ **Important**: In Google Drive, right-click your `VideoAutoUploader` folder → Share → add the service account email (looks like `video-uploader@your-project.iam.gserviceaccount.com`) with Editor access!

---

## 🔑 Step 2 — YouTube OAuth Token (Run Once on PC)

1. In Google Cloud Console → **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth 2.0 Client ID**
   - Application type: **Desktop app**
   - Name: `YouTube Uploader`
3. Download the JSON → rename it to `client_secrets.json`
4. Place `client_secrets.json` in the project root
5. Run this on your PC:
   ```bash
   pip install google-auth-oauthlib
   python auto-uploader/get_yt_token.py
   ```
6. A browser will open — **log in with your YouTube channel account**
7. Copy the entire content of `auto-uploader/youtube_token.json`
   — this is your `YOUTUBE_TOKEN_JSON` secret

---

## 🔑 Step 3 — Instagram Graph API Token

### 3a. Create Meta Developer App
1. Go to [developers.facebook.com](https://developers.facebook.com/)
2. Create App → **Business** type
3. Add product: **Instagram Graph API**

### 3b. Get Long-Lived Token
1. In your app → Instagram Graph API → **Generate Token**
2. Select your Instagram Creator account
3. Give permissions: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`
4. The token expires in 60 days — you need to refresh it manually

### 3c. Get your Instagram Account ID
```
https://graph.instagram.com/me?fields=id,username&access_token=YOUR_TOKEN
```
The `id` field = your `INSTAGRAM_ACCOUNT_ID`

---

## 🔑 Step 4 — Telegram Bot

1. Open Telegram → search **@BotFather**
2. Send: `/newbot`
3. Give it a name: `MrQuasar Uploader`
4. Copy the **token** — this is `TELEGRAM_BOT_TOKEN`
5. Start your bot (click the link BotFather sends)
6. Open [@userinfobot](https://t.me/userinfobot) → it sends you your **Chat ID**
   — this is `TELEGRAM_CHAT_ID`

---

## 🔑 Step 5 — Get Google Drive Folder ID

1. Open your `VideoAutoUploader` folder in Google Drive
2. Look at the URL: `https://drive.google.com/drive/folders/XXXXXXXXXXXXXXXXX`
3. The `XXXXXXXXXXXXXXXXX` part = your `GOOGLE_DRIVE_FOLDER_ID`

---

## 🐙 Step 6 — GitHub Setup

### 6a. Create GitHub Repository
1. Go to [github.com/new](https://github.com/new)
2. Name: `video-auto-uploader`
3. Set to **Public** (required for GitHub Pages)
4. Click **Create repository**

### 6b. Push code
```bash
cd "D:\project\Best video editro\auto-uploader"
git init
git add .
git commit -m "🚀 Initial setup"
git branch -M main
git remote add origin https://github.com/VJNAVEEN2005/video-auto-uploader.git
git push -u origin main
```

### 6c. Add GitHub Secrets
Go to: **Repository → Settings → Secrets and Variables → Actions → New Repository Secret**

Add each of these:

| Secret Name | Value |
|-------------|-------|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Entire JSON content from Step 1 |
| `YOUTUBE_CLIENT_ID` | From OAuth credentials |
| `YOUTUBE_CLIENT_SECRET` | From OAuth credentials |
| `YOUTUBE_TOKEN_JSON` | Content of youtube_token.json from Step 2 |
| `INSTAGRAM_ACCESS_TOKEN` | Token from Step 3 |
| `INSTAGRAM_ACCOUNT_ID` | Account ID from Step 3 |
| `TELEGRAM_BOT_TOKEN` | Token from Step 4 |
| `TELEGRAM_CHAT_ID` | Your chat ID from Step 4 |
| `GOOGLE_DRIVE_FOLDER_ID` | Folder ID from Step 5 |

---

## 🌐 Step 7 — Enable GitHub Pages (Dashboard)

1. In your repo → **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / folder: `/auto-uploader/dashboard`
4. Save

Your dashboard will be live at:
```
https://VJNAVEEN2005.github.io/video-auto-uploader/
```

### 7a. Update Dashboard with CSV File ID
After first upload runs:
1. Right-click `upload_log.csv` in Drive → Share → copy link
2. Extract the file ID from the URL
3. Open `dashboard/index.html` → replace `YOUR_UPLOAD_LOG_CSV_FILE_ID_HERE`
4. Commit and push

---

## 📹 Step 8 — Add Videos to Queue

For each video you want to auto-upload:

1. Create a folder in `VideoAutoUploader/Queue/` e.g. `06_My_New_Episode/`
2. Upload:
   - `video.mp4` — your vertical short (9:16 format)
   - `thumbnail.jpg` — your thumbnail
   - `meta.json` — copy from `TEMPLATE_meta.json`, fill in title/description
3. That's it! It uploads automatically at 7:30 PM IST 🎉

---

## ⚡ Manual Upload (Trigger Anytime)

Go to: **GitHub repo → Actions → Auto Upload Video → Run workflow**

You can optionally specify an episode name to force-upload a specific one.

---

## 📊 What the Dashboard Shows

| Column | Meaning |
|--------|---------|
| Total Uploaded | Videos successfully uploaded to both platforms |
| Failed | Upload attempts that had errors |
| In Queue | How many videos are waiting (update manually or via Drive) |
| Day Streak | Consecutive days with uploads |
| Countdown | Live timer to next 7:30 PM upload |
| History table | Every upload with YouTube + Instagram links |

---

## 🆘 Troubleshooting

| Problem | Fix |
|---------|-----|
| YouTube says "Token invalid" | Re-run `get_yt_token.py` and update `YOUTUBE_TOKEN_JSON` secret |
| Instagram "permission denied" | Refresh your Instagram access token (valid 60 days) |
| Dashboard shows "Could not load data" | Make `upload_log.csv` publicly shared in Drive |
| Action fails with "No videos in Queue" | Check folder name is exactly `Queue` and service account has access |
| Video not found on Drive | Make sure video is named `video.mp4` (not `short.mp4` etc.) |

---

## 📅 Upload Schedule

- **Time**: 7:30 PM IST (14:00 UTC) every day
- **Order**: Alphabetical by folder name (01_, 02_, 03_...)
- **After upload**: Folder moves from `Queue/` to `Uploaded/`
- **If fails**: Folder moves to `Failed/` + you get a Telegram alert

---

*Made for Mr.Quasar — VJNAVEEN2005*
