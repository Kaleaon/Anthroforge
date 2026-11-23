# AnthroForge Bot + Mini App — status

## Bot identity (verified 2026-11-12 via getMe)

- **Bot:** @anthroforge_bot — "AnthroForge"
- **Bot ID:** 9286298826
- **Link:** https://t.me/anthroforge_bot
- **Token:** `~/workspace/telegram-user/.private/bots/anthroforge.json` (mode 600; never printed, never copied here)
- Created via BotFather by `create_bot.py` (MTProto `tguser.make_client()` pattern, same as the family bots). First-choice username `anthroforge_bot` was available.
- Commands set + read back: `/start` (Welcome + open the creator), `/app` (Open the AnthroForge creator). Profile description + short description set from `create_bot.py`'s ABOUT_LONG / ABOUT_SHORT.
- Chat menu button: currently the default `commands` type — the **Web App menu button cannot be set until the Mini App has a live HTTPS URL** (see Blocker). Note (pass 2): even once set, a menu-button launch is *view-only* — `tg.sendData()` only delivers from a reply-keyboard launch, so the keyboard button below remains the save route.

## Components

| Piece | State |
|---|---|
| Mini App page (`index.html`) | ✅ Built + pass-2 fixes (2026-11-14). Telegram bridge now detects the launch mode: reply-keyboard launch → MainButton *Save character* via `sendData()`; inline/menu launch → view-only notice (copy the code instead). Shared `record.js` (`AFRecord.createRecordHelper`, exposed on `window.AFBuildRecord`) emits canonical Core records via `vocabulary.js` (bodyslide → canonical sliders, morph/sos/driver/head_shape/head_sculpt carried under `identity`, web bases → `af_body_neutral_v1`/`af_head_neutral_v2`). Import modal (AF1- paste + 6 canonical presets) wired via `record.js` to `decodeShareCode()`. "Save .afchar.json" replaced the bespoke Rig JSON (no loader existed). Mobile-first layout (viewport-fit=cover, single column, ≥44px targets, `@media (max-width: 1023.5px)`), "Copy share code (AF1-)" fallback button. Headless check at 375×812 done — layout renders correctly; the WebGL canvas region stays dark under headless SwiftShader (expected headless artifact; the scene init reports "32-Bone LBS Rig Ready"). |
| Share-code codec (`sharecode.js`) | ✅ Verified 2026-11-12: Node encode (canonical JSON + zlib-9 + CRC32 frame) → Python `core/sharecode.py` decode = lossless, sliders bit-exact incl. `0.30000000000000004` and `1e-09`. **Pass 2 added `decodeShareCode()`** (same frame/CRC/zlib, streaming `DecompressionStream` with `MAX_CODE_CHARS = 1,000,000` and `MAX_DECOMPRESSED_BYTES = 4,194,304` matching `core/sharecode.py`): loaded directly via `<script src>` by both `telegram-miniapp/index.html` and `anthroforge-v2/anthroforge_3d_pro_v2.html` (no inline JS copy). JS↔Python round-trips and size guards verified in `tests/test_sharecode_js.mjs`, incl. all 6 Python-generated preset codes decoding in JS. |
| Vocabulary + record helper (`core/vocabulary.py` + `vocabulary.js` + `record.js`) | ✅ Single translation table, Python (`core/vocabulary.py`) + JS (`vocabulary.js`) twins, loaded directly alongside `presets.js` and `record.js` by both `telegram-miniapp/index.html` and `anthroforge-v2/anthroforge_3d_pro_v2.html` (run local HTTP servers from the repository root so `../anthroforge-app/telegram-miniapp/` resolves in v2 HTML; `file://` opens also work in Chromium) and cross-checked by `tests/test_vocabulary.py`. Only the six `bodyslide.*` keys map to canonical sliders (approximate bridges, documented as such); `morph.*`/`sos.*`/`driver.*` are carried losslessly under `identity`; already-canonical `body.*`/`head.*` ids pass through; unknown web-prefixed ids are preserved under `identity.unmapped_sliders` with a warning; `record.js` preserves `id` (Crockford ULIDs), `name`, `species_preset.label`, `identity.head_shape`, and `identity.head_sculpt` across round-trips. End-to-end proof: a Mini App or v2 record → AF1- → Python decode → `Character.validate(registry)` = zero errors. |
| Bot backend (`bot.py`) | ✅ Running as systemd system service `anthroforge-bot.service` (installed + enabled via `ensure-running.sh`, unit source in `systemd/`). Long-polls: `/start`/`/app` → welcome + **reply-keyboard** Web App button (pass 2 — the inline button was removed; it could never save). `web_app_data` or a pasted `AF1-…` code → decoded by the app core, **validated against the canonical slider registry** (invalid records are refused with the errors named, not saved), saved to `received/<id>.afchar.json`, summary replied. **Backend NOT restarted after the pass-2 edit — restart is a follow-up (see below).** |
| Deployment (Vercel) | ⛔ **BLOCKED** — see below. No production URL yet; `app_url.txt` intentionally absent, so the bot's /start currently replies that the studio URL is still being wired up, while code-saving by paste works today. Deploy file list is now `index.html` + `sharecode.js` + `vocabulary.js` + `presets.js` + `record.js`. |
| Handoff to Joe | ✅ One message sent via @xynthetix_bot's existing DM thread (2026-11-12) with the t.me link + how to open it. Not sent by the original (interrupted) run — verified against the chat cache first. |

## Blocker: Vercel team-scope authorization

The Vercel connector is connected and authenticated, but every project/deployment call under Joe's team scope fails:

- Scope: `kaleaons-projects` — teamId `team_6yIssMyS648Jkbm6Mofb0DB0`
- `list_projects` / `create_project` → `403 forbidden — "You must re-authenticate to this scope or use a token with access to this scope"`; API recovery text asks for an `authorize_team_access` step.
- That tool is **not exposed** by this connector build (`/opt/hatch/bin/vercel call-tool --name authorize_team_access` → "unsupported Vercel tool"; `list_teams` returns empty), so the approval cannot be completed from the agent side.

**Joe action needed:** approve/re-authenticate team access for the Vercel connection (scope `kaleaons-projects`). Do NOT disconnect/reconnect — per the API guidance, approve team access on the existing connection.

### Once unblocked (5 steps, all scripted patterns already in place)

1. `create_project` (name `anthroforge-miniapp`, teamId above), then `create_deployment` with `index.html` + `sharecode.js` + `vocabulary.js` + `presets.js` + `record.js` targeting production.
2. Write the production URL to `app_url.txt` in this folder.
3. Bot API: `setChatMenuButton` → `{"type":"web_app","text":"Open AnthroForge","web_app":{"url":<URL>}}`; read back with `getChatMenuButton`. (Menu-button launches are view-only — the keyboard button from /start is the save route; the app says so in-room.)
4. `systemctl restart anthroforge-bot.service` (picks up `app_url.txt` for the /start keyboard button **and** the pass-2 bot.py changes — reply-keyboard launch + registry validation — which are currently live on disk but not yet in the running backend).
5. Joe taps the bot → Start → keyboard button opens the studio; "Save character" in the app returns the AF1- code to the chat and the backend files it under `received/`.

## What still waits on Joe (after the URL lands)

- His first tap: open https://t.me/anthroforge_bot → Start (a bot cannot message him first; the handoff DM from @xynthetix_bot carries the link).

## Pass 2 (2026-11-14) — what changed, in one place

- **Save transport (showstopper, fixed):** bot sends a reply-keyboard web_app button; the Mini App gates MainButton-save on the keyboard launch (`!tg.initData`) and shows a view-only notice otherwise. Verified against the real files (bot.py, index.html:3474/3555) — the plan's claim held exactly.
- **Vocabulary (fixed):** `core/vocabulary.py` + `vocabulary.js` + `record.js` shared across both UIs' record builders (desktop v2 loads `../anthroforge-app/telegram-miniapp/{sharecode,vocabulary,presets,record}.js` directly rather than carrying an inline twin). Preset import works from the 6 canonical presets; unknown web sliders are preserved, never dropped. One design correction made during the work: canonical `body.*`/`head.*` ids pass through translate unchanged — the first draft wrongly treated them as unmapped (caught by the new tests before anything shipped).
- **Share codes (fixed):** `decodeShareCode()` added to `sharecode.js`; Import AF1-/Preset modal in both UIs; desktop "Save Rig JSON" replaced by canonical `.afchar.json` (the bespoke format had no loader anywhere).
- **Tests:** full suite 97 passed (87 baseline + 10 new vocabulary tests); Node JS codec test passes (incl. Python-generated preset codes decoding in JS); end-to-end Mini App record → AF1- → Python decode → registry validation = zero errors. Backups: `~/workspace/anthroforge-app/backups/pass2-2026-11-14/` (bot.py, sharecode.js, index.html, anthroforge_3d_pro_v2.html).
- **Still to do (main-side, not this pass):** `systemctl restart anthroforge-bot.service` to load the pass-2 bot.py; Vercel team re-auth (Joe) for the deploy URL; a live end-to-end save from the deployed Mini App once the URL exists; DOUBLESIDE/loft winding (deferred in pass 1 — visual risk, needs an eyeball).
