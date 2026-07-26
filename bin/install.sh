#!/bin/bash
# launchd に登録する。 bin/uninstall.sh で解除。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.onod.adtech-news"
SRC="$ROOT/launchd/$LABEL.plist"
DST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_="$(id -u)"

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/logs" "$ROOT/out" "$ROOT/state"
if [[ ! -f "$ROOT/state/seen.json" ]]; then
  cp "$ROOT/state/seen.json.example" "$ROOT/state/seen.json"
fi
chmod +x "$ROOT/bin/run.sh"

cp "$SRC" "$DST"

launchctl bootout "gui/$UID_/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID_" "$DST"
launchctl enable "gui/$UID_/$LABEL"

echo "登録しました: $LABEL"
launchctl print "gui/$UID_/$LABEL" | grep -E 'state|next fire|path =' || true
echo
echo "手動実行:   $ROOT/bin/run.sh --force"
echo "解除:       $ROOT/bin/uninstall.sh"
