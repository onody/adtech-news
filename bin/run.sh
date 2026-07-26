#!/bin/bash
# adtech-news — 日次ダイジェストの生成と送信
#
#   run.sh                       生成して送信（平日のみ）
#   run.sh --dry-run             生成するが送信しない（state も更新しない）
#   run.sh --date 2026-07-28     日付を指定
#   run.sh --send-only           既存の out/<date>.json を送信するだけ
#   run.sh --force               土日でも実行する

set -euo pipefail

export PATH="/Users/onod/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck source=/dev/null
source "$ROOT/config.sh"

DRY_RUN=0
SEND_ONLY=0
FORCE=0
DATE="$(date +%F)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)   DRY_RUN=1; shift ;;
    --send-only) SEND_ONLY=1; shift ;;
    --force)     FORCE=1; shift ;;
    --date)      DATE="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$ROOT/out" "$ROOT/logs" "$ROOT/state"
LOG="$ROOT/logs/$DATE.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== adtech-news $DATE $(date +%T) ==="

DOW="$(date -j -f %Y-%m-%d "$DATE" +%u 2>/dev/null || date +%u)"
if [[ "$DOW" -ge 6 && "$FORCE" -eq 0 ]]; then
  echo "土日のためスキップ (dow=$DOW)。--force で実行できます。"
  exit 0
fi

DIGEST="$ROOT/out/$DATE.json"

if [[ "$SEND_ONLY" -eq 0 ]]; then
  [[ -f "$ROOT/state/seen.json" ]] || echo '{"entries":[]}' > "$ROOT/state/seen.json"

  PROMPT="$(sed -e "s|{{DATE}}|$DATE|g" -e "s|{{ITEM_COUNT}}|$ITEM_COUNT|g" \
             "$ROOT/prompts/digest.md")"

  echo "--- 生成開始 (model=$MODEL, budget=\$$MAX_BUDGET_USD) ---"
  set +e
  /usr/bin/perl -e 'alarm shift; exec @ARGV' "$GEN_TIMEOUT" \
    claude -p "$PROMPT" \
      --model "$MODEL" \
      --permission-mode bypassPermissions \
      --allowedTools "WebSearch,WebFetch,Read,Write" \
      --disallowedTools "Bash,Task,Agent,Edit,NotebookEdit" \
      --max-budget-usd "$MAX_BUDGET_USD" \
      --no-session-persistence \
      --output-format text
  GEN_RC=$?
  set -e
  echo "--- 生成終了 (rc=$GEN_RC) ---"

  if [[ ! -f "$DIGEST" ]]; then
    echo "ERROR: $DIGEST が生成されませんでした" >&2
    exit 1
  fi
fi

if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$DIGEST"; then
  echo "ERROR: $DIGEST が不正な JSON です" >&2
  exit 1
fi

python3 "$ROOT/lib/render.py" "$DIGEST"

SEND_ARGS=(
  "$DIGEST"
  --to "$RECIPIENT"
  --sender "$SENDER"
  --sender-name "$SENDER_NAME"
  --keychain-service "$KEYCHAIN_SERVICE"
  --state "$ROOT/state/seen.json"
)
[[ "$DRY_RUN" -eq 1 ]] && SEND_ARGS+=(--dry-run)

python3 "$ROOT/lib/send.py" "${SEND_ARGS[@]}"

echo "=== done $(date +%T) ==="
