---
name: impl-api
description: API設計書IDから FastAPI バックエンド実装を行うスラッシュコマンド
---

# /impl-api <API-ID>

`.agent/prompts/build/PRM-BLD-API-001.md` の手順に従い、指定された API 設計書からサーバー実装を行います。

## 自動ドキュメント読み込みルール
- 本コマンド呼び出し時、エージェントは指定された `<API-ID>` に対応する設計書（`docs/30_detail-design/api/API-XXXX-*.md`）を開き、そのフロントマター内の `consumes`（`UC-XXXX`, `TBL-XXXX`, `MSG-0001`, `REQ-0003` 等）に定義された全ての依存ドキュメントを**自動的に `view_file` でコンテキストへロードしてから実装を開始**します。

## 制約
- テストコードは書きません (`/write-tests` を使用すること)
- `docs/` ディレクトリを直接編集しません
- 設計書にないエラーコードや業務ルールを新設しません
