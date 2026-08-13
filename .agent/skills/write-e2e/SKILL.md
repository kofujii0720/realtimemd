---
name: write-e2e
description: 画面設計書から E2E テストを作成するスラッシュコマンド
---

# /write-e2e <SCR-ID>

`.agent/prompts/test/PRM-TST-E2E-001.md` の手順に従い、Playwright E2E テストを作成します。

## 制約
- 実装より先に作成し、落ちる状態 (FAIL) でセッションを終了させます
- 要素選択には `data-testid` のみを使用します
