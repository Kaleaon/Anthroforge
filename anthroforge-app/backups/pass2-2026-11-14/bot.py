#!/usr/bin/env python3
"""AnthroForge bot backend — deliberately minimal.

Long-polls the dedicated AnthroForge bot (@anthroforge_bot):
- /start or /app  -> welcome + inline Web App button (URL from app_url.txt)
- web_app_data    -> an AF1- share code from the Mini App: decode it with
                     the anthroforge-app core, save the character record
                     to received/<id>.afchar.json, reply with a summary.
- a bare AF1-... text message is treated the same as web_app_data.

Token is read from ~/workspace/telegram-user/.private/bots/anthroforge.json
on each start and is never printed or logged. Stdlib only.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = "/home/hatch/workspace/telegram-user/.private/bots/anthroforge.json"
RECEIVED = os.path.join(HERE, "received")
OFFSET_FILE = os.path.join(HERE, ".offset")
APP_ROOT = "/home/hatch/workspace/anthroforge-app"
sys.path.insert(0, APP_ROOT)

from core import sharecode  # noqa: E402
from core.errors import ShareCodeError  # noqa: E402


def load_token():
    with open(TOKEN_FILE) as f:
        return json.load(f)["token"]


TOKEN = load_token()
API = f"https://api.telegram.org/bot{TOKEN}/"


def app_url():
    try:
        with open(os.path.join(HERE, "app_url.txt")) as f:
            url = f.read().strip()
            if url.startswith("https://"):
                return url
    except OSError:
        pass
    return None


def api(method, params=None, timeout=45):
    body = urllib.parse.urlencode({
        k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
        for k, v in (params or {}).items()
    }).encode()
    req = urllib.request.Request(API + method, data=body)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def send(chat_id, text, reply_markup=None):
    params = {"chat_id": chat_id, "text": text}
    if reply_markup:
        params["reply_markup"] = reply_markup
    try:
        api("sendMessage", params, timeout=30)
    except Exception as exc:  # never let a reply failure kill the loop
        print(f"sendMessage failed: {exc}", flush=True)


WELCOME = (
    "🦊 *AnthroForge* — the Titan family's avatar creator.\n\n"
    "Build a furry character in the 3D studio: species presets, morph / "
    "BodySlide / SoS sliders, modular parts. When you tap *Save character* "
    "in the app, your character lands here as a portable share code.\n\n"
    "Commands: /app opens the creator."
)


def handle_start(chat_id):
    url = app_url()
    markup = None
    if url:
        markup = {"inline_keyboard": [[
            {"text": "🦊 Open AnthroForge", "web_app": {"url": url}}
        ]]}
    text = WELCOME
    if not url:
        text += "\n\n(The studio URL is still being wired up — check back in a moment.)"
    send(chat_id, text, markup)


def summarise(code, chat_id):
    try:
        ch = sharecode.decode(code)
    except (ShareCodeError, Exception) as exc:  # decode raises named errors
        send(chat_id, f"⛔ That share code didn't decode: {exc}")
        return
    os.makedirs(RECEIVED, exist_ok=True)
    path = ch.save(os.path.join(RECEIVED, f"{ch.id}.afchar.json"))
    sliders = ch.sliders
    headline = []
    for key in ("morph.height", "morph.ears", "morph.torso", "bodyslide.samson",
                    "bodyslide.samuel"):
        if key in sliders:
            headline.append(f"{key.split('.', 1)[1]} {sliders[key]:g}")
    species = (ch.species_preset or {}).get("preset") or ch.identity.get("species") or "custom"
    lines = [
        "✅ *Character saved!*",
        f"Name: {ch.name}",
        f"ID: `{ch.id}`",
        f"Species preset: {species}",
        f"Sliders set: {len(sliders)} · Parts equipped: {len(ch.parts)}",
    ]
    if headline:
        lines.append("Headline: " + " · ".join(headline))
    lines.append(f"Stored as {os.path.basename(path)} — send the AF1- code any time to re-open it.")
    send(chat_id, "\n".join(lines))


def handle_update(upd):
    msg = upd.get("message") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    if chat_id is None:
        return
    wad = msg.get("web_app_data")
    if wad and wad.get("data"):
        summarise(wad["data"].strip(), chat_id)
        return
    text = (msg.get("text") or "").strip()
    if text.startswith("/start") or text.startswith("/app"):
        handle_start(chat_id)
    elif text.startswith("AF1-"):
        summarise(text, chat_id)
    elif text:
        send(chat_id, "Send /app to open the creator, or paste an AF1- share code and I'll save that character.")


def main():
    offset = 0
    try:
        offset = int(open(OFFSET_FILE).read().strip())
    except Exception:
        offset = 0
    print("anthroforge bot backend polling…", flush=True)
    while True:
        try:
            resp = api("getUpdates", {
                "offset": offset, "timeout": 30,
                "allowed_updates": ["message"],
            }, timeout=45)
            for upd in resp.get("result", []):
                offset = upd["update_id"] + 1
                try:
                    with open(OFFSET_FILE, "w") as f:
                        f.write(str(offset))
                except OSError:
                    pass
                handle_update(upd)
        except Exception as exc:
            print(f"poll error: {exc}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
