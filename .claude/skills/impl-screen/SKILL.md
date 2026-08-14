---
name: impl-screen
description: 画面設計書IDから React フロントエンド画面を実装するスラッシュコマンド
---

# /impl-screen <SCR-ID>

`.agent/prompts/build/PRM-BLD-SCR-001.md` の手順に従い、指定された画面設計書から画面実装を行います。

## 自動ドキュメント読み込みルール
- 本コマンド呼び出し時、エージェントは指定された `<SCR-ID>` に対応する画面設計書（`docs/20_basic-design/screen/SCR-XXXX-*.md`）を開き、そのフロントマター内の `consumes` および `calls_apis`（`UC-XXXX`, `API-XXXX`, `MSG-0001`, `REQ-0003` 等）に定義された全ての依存ドキュメントを**自動的に `view_file` でコンテキストへロードしてから実装を開始**します。

## 制約
- 読込中 / 0件 / 正常 / エラー の4状態全てを必ず実装します
- `data-testid` は設計書の文字列そのままを要素に付与します
