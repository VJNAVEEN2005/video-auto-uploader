"""
telegram_notifier.py — Send upload notifications to your Telegram bot.
"""

import requests


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.token   = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send(self, message: str) -> bool:
        """
        Send a markdown message to your Telegram chat.

        Episode titles are free text and can contain characters that Telegram's
        Markdown parser rejects (#Shorts, stray * or _), which returns 400. Fall
        back to plain text so a notification is never lost over formatting.
        """
        try:
            r = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id":    self.chat_id,
                    "text":       message,
                    "parse_mode": "Markdown"
                },
                timeout=15
            )
            if r.status_code == 400:
                print("   ⚠️  Markdown rejected (bad title formatting) - retrying as plain text")
                r = requests.post(
                    f"{self.api_url}/sendMessage",
                    json={"chat_id": self.chat_id, "text": message},
                    timeout=15
                )
            r.raise_for_status()
            print(f"📨 Telegram notification sent!")
            return True
        except Exception as e:
            print(f"⚠️  Telegram notification failed: {e}")
            return False
