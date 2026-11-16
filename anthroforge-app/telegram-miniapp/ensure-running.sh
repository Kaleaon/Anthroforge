#!/bin/sh
# Idempotent keeper for the AnthroForge bot backend (same pattern as
# ~/workspace/telegram-user/ensure-running.sh): unit source lives here in
# the workspace; this copies it into /etc/systemd/system if changed,
# daemon-reloads, enables, and starts the service if not active.
set -e
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
u=anthroforge-bot
if ! cmp -s "$ROOT/systemd/$u.service" "/etc/systemd/system/$u.service" 2>/dev/null; then
  cp "$ROOT/systemd/$u.service" "/etc/systemd/system/$u.service"
  systemctl daemon-reload
fi
systemctl enable "$u.service" >/dev/null 2>&1 || true
systemctl is-active --quiet "$u.service" || systemctl restart "$u.service" || true
echo "$u: $(systemctl is-active "$u.service" 2>/dev/null || echo unknown)"
