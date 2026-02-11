#!/usr/bin/env python3
"""Send notifications via Discord Webhook.
Usage: ./notify_status.py "Title" "Message" [Color: green|red|yellow]

Configuration:
- Looks for DISCORD_WEBHOOK_URL in environment variable.
- Or fails gracefully if not found (logs to stdout).
"""

import os
import sys
import json
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError

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

def send_discord_message(title, message, color_name="green"):
    if not WEBHOOK_URL:
        print(f"[Create Discord Webhook] {title}: {message}")
        print("Tip: Set DISCORD_WEBHOOK_URL to enable real notifications.")
        return

    color = COLORS.get(color_name, COLORS["green"])
    
    payload = {
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color,
                "footer": {
                    "text": f"Goyoonjung Wiki Automation • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
        ]
    }
    
    req = Request(
        WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with urlopen(req) as response:
            if response.status == 204:
                print("Notification sent successfully.")
            else:
                print(f"Notification sent but unexpected status: {response.status}")
    except URLError as e:
        print(f"Failed to send notification: {e}")

def main():
    if len(sys.argv) < 3:
        print("Usage: notify_status.py <Title> <Message> [Color]")
        sys.exit(1)
        
    title = sys.argv[1]
    message = sys.argv[2]
    color = sys.argv[3] if len(sys.argv) > 3 else "green"
    
    send_discord_message(title, message, color)

if __name__ == "__main__":
    main()
