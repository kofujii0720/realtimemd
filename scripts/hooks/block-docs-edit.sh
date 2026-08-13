#!/usr/bin/env bash
# scripts/hooks/block-docs-edit.sh
# 実装中の docs/ 直接編集をブロックする PreToolUse フック

TARGET_FILE="$1"

# ALLOW_DOCS_EDIT=1 がセットされている場合は通過（設計変更専用セッション用）
if [ "${ALLOW_DOCS_EDIT}" = "1" ]; then
  exit 0
fi

# ターゲットファイルが docs/ 以下であり、かつ docs/reviews/ 以外の場合ブロック
if [[ "${TARGET_FILE}" == *"docs/"* ]] && [[ "${TARGET_FILE}" != *"docs/reviews/"* ]]; then
  echo "[HOOK ERROR] 実装セッション中に docs/ を直接編集することは禁止されています。" >&2
  echo "設計変更は別セッションで行うか、ALLOW_DOCS_EDIT=1 を指定してください。" >&2
  exit 2
fi

exit 0
