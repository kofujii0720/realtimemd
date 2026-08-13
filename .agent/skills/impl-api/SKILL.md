---
name: impl-api
description: API設計書IDから FastAPI バックエンド実装を行うスラッシュコマンド
---

# /impl-api <API-ID>

`.agent/prompts/build/PRM-BLD-API-001.md` の手順に従い、指定された API 設計書からサーバー実装を行います。

## 制約
- テストコードは書きません (`/write-tests` を使用すること)
- `docs/` ディレクトリを直接編集しません
- 設計書にないエラーコードや業務ルールを新設しません
