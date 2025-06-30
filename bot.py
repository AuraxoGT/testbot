import os
import json
import requests
from fastapi import FastAPI, Request, Header, HTTPException
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# Load secrets from environment
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not DISCORD_PUBLIC_KEY or not DISCORD_BOT_TOKEN:
    raise ValueError("Missing DISCORD_PUBLIC_KEY or DISCORD_BOT_TOKEN in environment variables.")

app = FastAPI()

@app.post("/")
async def interactions(
    request: Request,
    x_signature_ed25519: str = Header(...),
    x_signature_timestamp: str = Header(...)
):
    body = await request.body()

    # Signature verification
    try:
        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(
            x_signature_timestamp.encode() + body,
            bytes.fromhex(x_signature_ed25519)
        )
    except BadSignatureError:
        raise HTTPException(status_code=401, detail="Invalid request signature.")

    data = await request.json()

    # Discord PING check
    if data.get("type") == 1:
        return {"type": 1}

    # Slash command interaction
    if data.get("type") == 2:
        user_id = data["member"]["user"]["id"]
        success = send_dm(user_id, "👋 Pong from a dotless bot!")

        return {
            "type": 4,
            "data": {
                "content": "✅ DM sent!" if success else "⚠️ Failed to send DM."
            }
        }

def send_dm(user_id: str, message: str) -> bool:
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    # Open DM channel
    r = requests.post(
        "https://discord.com/api/v10/users/@me/channels",
        headers=headers,
        json={"recipient_id": user_id}
    )

    if r.status_code != 200:
        print(f"Failed to open DM channel: {r.status_code} {r.text}")
        return False

    channel_id = r.json().get("id")
    r2 = requests.post(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        headers=headers,
        json={"content": message}
    )

    if r2.status_code != 200:
        print(f"Failed to send DM: {r2.status_code} {r2.text}")
        return False

    return True
