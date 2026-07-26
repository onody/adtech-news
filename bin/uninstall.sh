#!/bin/bash
set -euo pipefail
LABEL="com.onod.adtech-news"
UID_="$(id -u)"
launchctl bootout "gui/$UID_/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
echo "解除しました: $LABEL"
