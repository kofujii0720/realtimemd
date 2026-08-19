---
schema_version: 1
id: BUG-2026-0005
detected_phase: REVIEW
detected_at: 2026-08-19T22:52:29+09:00
detected_by: agent
target_artifact: MSG-0001
artifact_type: design
severity: low
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
`MSG-0001`（メッセージ辞書）の「1. メッセージ一覧」の備考欄に記載されているエラーコード一覧が、実際の各API設計書のエラー定義と一致していない。
- `error.document.notFound` の備考に `E-0101-001` が記載されているが、`API-0101` の `E-0101-001` はクエリパラメータ制約違反。
- `error.document.sizeExceeded` の備考に `API-0201` の `E-0201-001`（入力サイズ超過）が未記載。
- `error.common.systemError` の備考に `E-0401-999` のみが記載され、各API共通の `E-010x-999` / `E-0201-999` が未記載。

# 再現手順
1. `docs/20_basic-design/MSG-0001-messages.md` の「1. メッセージ一覧」の備考欄を確認する。
2. `docs/30_detail-design/api/API-0101-document-list.md`, `docs/30_detail-design/api/API-0201-preview-render.md` などのエラー定義と照合する。

# 原因
API設計書の新規作成・改定時に、メッセージ辞書の備考欄の参照一覧の同期メンテナンスが行われていなかった。

# 恒久対策
> 恒久対策には「この指摘が二度と出ないようにするために、
> どのプロンプト / 規約 / 観点表を直すか」を必ず書く。

1. `MSG-0001` の備考欄を最新の各API定義と同期修正する。
2. `node scripts/check-docs.mjs` に、メッセージ辞書の備考欄と各API設計書のエラー定義との双方向検証機能を追加する。
