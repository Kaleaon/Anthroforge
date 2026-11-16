#!/usr/bin/env python3
"""Create the dedicated AnthroForge bot via BotFather, following the
proven family-bot process (BOT_CREATION_RUN_2026-11-06.md): MTProto via
tguser.make_client() (guarded session), history-polling for BotFather
replies, token saved ONLY to .private/bots/anthroforge.json (mode 600),
never printed. Run with the telegram-user venv python.
"""
import asyncio
import json
import os
import re
import sys
import time

TG_ROOT = "/home/hatch/workspace/telegram-user"
sys.path.insert(0, TG_ROOT)
from tguser import make_client  # noqa: E402

TOKEN_RE = re.compile(r"(\d{6,12}):([A-Za-z0-9_-]{30,})")
BOT_DIR = os.path.join(TG_ROOT, ".private", "bots")
DISPLAY = "AnthroForge"
USERNAMES = [
    "anthroforge_bot",
    "anthroforge_app_bot",
    "anthroforge_mini_bot",
    "xynthetix_anthroforge_bot",
]
ABOUT_SHORT = (
    "Avatar creator for the Titan family — build, save, and share furry characters."
)
ABOUT_LONG = (
    "AnthroForge is the Titan family's avatar creator: a real skinned 3D "
    "studio in a Telegram Mini App. Pick a species preset, sculpt with "
    "morph / BodySlide / SoS sliders, equip modular parts, then save your "
    "character — it arrives here as a portable AF1- share code you can "
    "re-open, share, or export to GLB.\n\nTap the menu button (or /app) "
    "to open the creator."
)


async def last_id(client, bf):
    msgs = await client.get_messages(bf, limit=1)
    return msgs[0].id if msgs else 0


async def wait_reply(client, bf, bf_id, after_id, timeout=90):
    start = time.time()
    while time.time() - start < timeout:
        msgs = await client.get_messages(bf, limit=8)
        cands = [m for m in msgs
                 if m.id > after_id and m.sender_id == bf_id and (m.text or "")]
        if cands:
            return sorted(cands, key=lambda x: x.id)[0]
        await asyncio.sleep(1.5)
    raise TimeoutError(f"no BotFather reply within {timeout}s (after_id={after_id})")


async def main():
    client = make_client()
    await client.start()
    try:
        bf = await client.get_entity("BotFather")
        bf_id = bf.id
        before = await last_id(client, bf)
        await client.send_message(bf, "/newbot")
        r = await wait_reply(client, bf, bf_id, before)
        if "call it" not in (r.text or ""):
            raise RuntimeError(f"unexpected /newbot reply: {(r.text or '')[:200]!r}")
        before = r.id
        await client.send_message(bf, DISPLAY)
        r = await wait_reply(client, bf, bf_id, before)
        if "username" not in (r.text or "").lower():
            raise RuntimeError(f"unexpected name-step reply: {(r.text or '')[:200]!r}")

        token = None
        bot_id = None
        username_used = None
        for username in USERNAMES:
            before = r.id
            await client.send_message(bf, username)
            r = await wait_reply(client, bf, bf_id, before)
            text = r.text or ""
            m = TOKEN_RE.search(text)
            if not m:
                try:
                    r2 = await wait_reply(client, bf, bf_id, r.id, timeout=20)
                    m = TOKEN_RE.search(r2.text or "")
                    if m:
                        r, text = r2, r2.text or ""
                except TimeoutError:
                    pass
            if m:
                token = m.group(0)
                bot_id = m.group(1)
                username_used = username
                break
            low = text.lower()
            if "taken" in low or "already" in low or "invalid" in low or "not valid" in low:
                print(f"username {username} refused: {text[:120]!r}", flush=True)
                continue
            raise RuntimeError(f"unexpected username-step reply for {username}: {text[:200]!r}")
        if not token:
            raise RuntimeError("all username choices refused by BotFather")

        path = os.path.join(BOT_DIR, "anthroforge.json")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump({"name": "anthroforge", "username": username_used,
                       "display_name": DISPLAY, "token": token,
                       "bot_id": str(bot_id)}, f, indent=1)
        os.chmod(path, 0o600)
        print(f"CREATED @{username_used} id {bot_id}; token saved (600)", flush=True)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
