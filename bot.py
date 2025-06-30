import os
import json
import hmac
import hashlib
import time
import requests
from fastapi import FastAPI, Request, Header
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
APP_ID = os.getenv("DISCORD_APP_ID")

app = FastAPI()

@app.post("/")
async def interactions(request: Request, x_signature_ed25519: str = Header(...), x_signature_timestamp: str = Header(...)):
    body = await request.body()

    try:
        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(
            x_signature_timestamp.encode() + body,
            bytes.fromhex(x_signature_ed25519)
        )
    except BadSignatureError:
        return {"error": "invalid request signature"}

    data = await request.json()

    if data["type"] == 1:
        return {"type": 1}  # Pong for PING

    if data["type"] == 2:  # Slash command
        user_id = data["member"]["user"]["id"]
        send_dm(user_id, "👋 Pong from a dotless bot!")
        return {
            "type": 4,
            "data": {
                "content": "✅ DM sent!"
            }
        }

def send_dm(user_id, message):
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    # Create DM channel
    r = requests.post("https://discord.com/api/v10/users/@me/channels", headers=headers, json={"recipient_id": user_id})
    if r.status_code == 200:
        channel_id = r.json()["id"]
        requests.post(f"https://discord.com/api/v10/channels/{channel_id}/messages",
                      headers=headers, json={"content": message})

    else:
        print(f"Failed to open DM: {r.status_code} {r.text}")
