---
schema_version: 1
id: BUG-2026-0003
detected_phase: REVIEW
detected_at: 2026-08-19T22:52:29+09:00
detected_by: agent
target_artifact: API-0103
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
`API-0103`（ドキュメント更新API）の入力制約（2.1）では `title` は `1〜255文字` と規定されているが、エラー定義（2.3）には未入力・空用の `E-0103-003` のみが定義されており、上限（255文字）を超過した場合のエラーコード（`E-0103-004`）が定義されていない。

# 再現手順
1. `docs/30_detail-design/api/API-0103-document-update.md` の「2.1 入力」を確認する（`title` の制約: 1〜255文字）。
2. 同文書の「2.3 エラー」を確認する（タイトル未入力の `E-0103-003` のみ定義され、255文字超過時のエラーコードが未定義）。

# 原因
入力制約（下限値・上限値）からエラーコードを網羅的に導出する際、下限（空文字列）のみを抽出し、上限（255文字超過）のエラーコード導出が漏れていた。

# 恒久対策
> 恒久対策には「この指摘が二度と出ないようにするために、
> どのプロンプト / 規約 / 観点表を直すか」を必ず書く。

1. `API-0103` の「2.3 エラー」に `E-0103-004`（条件: タイトル文字数制限(255文字)超過, HTTP 400, messageKey: `error.document.titleTooLong`）を追加する。
2. API設計書作成プロンプト（`PRM-IMPL-API-001.md`）および `VP-API-COMMON`（観点 `VP-002`）に基づき、全入力項目の上限・下限バリデーションに対するエラーコード定義の100%網羅を義務付ける。
