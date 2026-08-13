---
name: impl-screen
description: 画面設計書IDから React フロントエンド画面を実装するスラッシュコマンド
---

# /impl-screen <SCR-ID>

`.agent/prompts/build/PRM-BLD-SCR-001.md` の手順に従い、指定された画面設計書から画面実装を行います。

## 制約
- 読込中 / 0件 / 正常 / エラー の4状態全てを必ず実装します
- `data-testid` は設計書の文字列そのままを要素に付与します
