#!/usr/bin/env bash
# scripts/hooks/stop-check-docs.sh
# ターン終了時に設計書整合性をチェックする Stop フック

node scripts/check-docs.mjs
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "[HOOK ERROR] 設計書の整合性チェック(L6センサー)が失敗しています。修正してください。" >&2
  exit 2
fi

exit 0
