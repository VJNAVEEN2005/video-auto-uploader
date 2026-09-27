"""
get_yt_token.py — Run this ONCE on your PC to generate youtube_token.json
This token is then stored as a GitHub Secret (YOUTUBE_TOKEN_JSON).

Run:  python auto-uploader/get_yt_token.py
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

def main():
    # You need to download client_secrets.json from Google Cloud Console
    # APIs & Services → Credentials → OAuth 2.0 Client IDs → Download JSON
    client_secrets = "client_secrets.json"

    if not os.path.exists(client_secrets):
        print("❌ client_secrets.json not found!")
        print("\nSteps to get it:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. APIs & Services → Credentials")
        print("3. Create OAuth 2.0 Client ID (Desktop App)")
        print("4. Download JSON → rename to client_secrets.json")
        print("5. Place it next to this script")
        return

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
    creds = flow.run_local_server(port=0)

    token_data = {
        "token":         creds.token,
        "refresh_token": creds.refresh_token,
    }

    with open("auto-uploader/youtube_token.json", "w") as f:
        json.dump(token_data, f, indent=2)

    print("\n✅ youtube_token.json saved!")
    print("\nNext step: Copy the ENTIRE content of youtube_token.json")
    print("and paste it as a GitHub Secret named: YOUTUBE_TOKEN_JSON")
    print("\nContent:")
    print(json.dumps(token_data, indent=2))

if __name__ == "__main__":
    main()
