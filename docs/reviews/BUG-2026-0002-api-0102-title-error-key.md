---
schema_version: 1
id: BUG-2026-0002
detected_phase: REVIEW
detected_at: 2026-08-19T22:52:29+09:00
detected_by: agent
target_artifact: API-0102
artifact_type: design
severity: medium
cause_phase: DESIGN
cause_category: design-miss
root_cause_viewpoint: null
prompt_file: .agent/prompts/review/PRM-REV-DOC-001.md
fix_method: doc-update
status: closed
detected_sprint: null
closed_at: 2026-08-19T23:01:00+09:00
effort_hours: 0.2
---

# 事象
`API-0102`（ドキュメント新規作成API）のエラー定義「2.3 エラー」において、`E-0102-002`（条件: タイトル文字数制限255文字超過）の messageKey に `MSG-0001.key.error.document.titleRequired`（日本語メッセージ: 「ドキュメントタイトルは必須です。」）が指定されている。
これにより、タイトル文字数超過時に「タイトルが必須」という不整合なメッセージが返却される。

# 再現手順
1. `docs/30_detail-design/api/API-0102-document-create.md` の「2.3 エラー」を確認する（`E-0102-002` の messageKey が `MSG-0001.key.error.document.titleRequired`）。
2. `docs/20_basic-design/MSG-0001-messages.md` の「1. メッセージ一覧」を確認する（`error.document.titleRequired` の文言が「ドキュメントタイトルは必須です。」）。

# 原因
タイトルバリデーションエラー設計時に、タイトル必須エラー用のメッセージキーを流用してしまい、文字数超過専用のメッセージキー定義およびマッピングが漏れていた。

# 恒久対策
> 恒久対策には「この指摘が二度と出ないようにするために、
> どのプロンプト / 規約 / 観点表を直すか」を必ず書く。

1. `MSG-0001` にキー `error.document.titleTooLong`（「ドキュメントタイトルは255文字以内で入力してください。」）を追加する。
2. `API-0102` の `E-0102-002` の messageKey を新設キー `error.document.titleTooLong` に修正する。
3. API設計作成プロンプトおよび `VP-API-COMMON`（観点 `VP-004`）において、エラー条件と割り当てる messageKey の意味的一致を検証するセルフチェック項目を強化する。
