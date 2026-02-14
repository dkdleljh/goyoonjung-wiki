#!/usr/bin/env python3
"""Send notifications via Discord Webhook.
Usage: ./notify_status.py "Title" "Message" [Color: green|red|yellow]

Configuration:
- Looks for DISCORD_WEBHOOK_URL in environment variable.
- Or fails gracefully if not found (logs to stdout).
"""

import json
import os
import sys
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request, urlopen

# Configuration
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config_loader

CONF = config_loader.load_config()
# Priority: Config > Env
WEBHOOK_URL = CONF.get('discord_webhook_url') or os.environ.get("DISCORD_WEBHOOK_URL")

COLORS = {
    "green": 5763719,  # Success
    "red": 15548997,   # Failure
    "yellow": 16776960 # Warning
}

def queue_notification(title: str, message: str, color_name: str) -> None:
    try:
        import json
        from pathlib import Path
        base = Path(__file__).resolve().parent.parent
        q = base / '.locks' / 'notify-queue.jsonl'
        q.parent.mkdir(parents=True, exist_ok=True)
        item = {"title": title, "message": message, "color": color_name}
        with q.open('a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    except Exception:
        pass


def send_discord_message(title, message, color_name="green", force: bool = False):
    if not WEBHOOK_URL:
        print(f"[Create Discord Webhook] {title}: {message}")
        print("Tip: Set DISCORD_WEBHOOK_URL to enable real notifications.")
        return False

    color = COLORS.get(color_name, COLORS["green"])

    payload = {
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color,
                "footer": {
                    "text": f"고윤정 위키 자동화 • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
        ]
    }

    req = Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    )

    # Retry a few times; queue on failure
    import time
    for attempt in range(1, 4):
        try:
            with urlopen(req, timeout=10) as response:
                if response.status == 204:
                    print("Notification sent successfully.")
                    return True
                else:
                    print(f"Notification sent but unexpected status: {response.status}")
                    return True
        except URLError as e:
            print(f"Failed to send notification (attempt {attempt}/3): {e}")
            time.sleep(1.5 * attempt)
        except Exception as e:
            print(f"Failed to send notification (attempt {attempt}/3): {e}")
            time.sleep(1.5 * attempt)

    # If we reach here, all attempts failed
    queue_notification(title, message, color_name)
    return False

def main():
    if len(sys.argv) < 3:
        print("Usage: notify_status.py <Title> <Message> [Color]")
        sys.exit(1)

    title = sys.argv[1]
    message = sys.argv[2]
    color = sys.argv[3] if len(sys.argv) > 3 else "green"

    ok = send_discord_message(title, message, color)
    # exit nonzero if not delivered (so callers can notice in logs)
    if not ok:
        sys.exit(2)

if __name__ == "__main__":
    main()
