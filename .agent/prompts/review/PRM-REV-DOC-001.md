---
id: PRM-REV-DOC-001
name: 設計書レビュープロンプト正本
phase: review
activity: 設計書のセルフチェックおよび整合性検証を行う
inputs:
  - path: docs/**/*.md
    required: true
version: 1
---

# 手順
1. `node scripts/check-docs.mjs` を実行する。
2. 契約・参照・エラーコードの不整合がないかを報告する。
