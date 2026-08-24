#!/usr/bin/env bash
# Launch a dedicated Chrome audit desktop for the target origin.
# Usage: ORIGIN=https://platform.opulentia.ai ./start_audit_desktop.sh

set -euo pipefail

ORIGIN="${ORIGIN:-https://platform.opulentia.ai}"
PORT="${CDP_PORT:-9223}"
PROFILE="${AUDIT_PROFILE:-/tmp/opulent-audit}}

mkdir -p "$PROFILE"

# Determine Chrome binary. Override with CHROME_BIN if needed.
if [ -n "${CHROME_BIN:-}" ]; then
  CHROME="$CHROME_BIN"
elif command -v google-chrome &>/dev/null; then
  CHROME="google-chrome"
elif [ -x "/opt/.devin/chrome/linux-133.0.6943.126/chrome-linux64/chrome" ]; then
  CHROME="/opt/.devin/chrome/linux-133.0.6943.126/chrome-linux64/chrome"
else
  echo "Cannot find Chrome. Set CHROME_BIN." >&2
  exit 1
fi

exec "$CHROME" \
  --remote-debugging-port="$PORT" \
  --remote-allow-origins='*' \
  --user-data-dir="$PROFILE" \
  --no-first-run \
  --no-default-browser-check \
  --enable-automation \
  --password-store=basic \
  --disable-features=PasswordManager \
  --disable-infobars \
  --disable-popup-blocking \
  "$ORIGIN/auth?mode=signup"
