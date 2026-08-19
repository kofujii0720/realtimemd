---
schema_version: 1
id: BUG-2026-0001
detected_phase: REVIEW
detected_at: 2026-08-19T22:52:29+09:00
detected_by: agent
target_artifact: SCR-0101
artifact_type: design
severity: high
cause_phase: DESIGN
cause_category: design-miss
root_cause_viewpoint: null
prompt_file: .agent/prompts/review/PRM-REV-DOC-001.md
fix_method: doc-update
status: closed
detected_sprint: null
closed_at: 2026-08-19T23:01:00+09:00
effort_hours: 0.5
---

# 事象
`SCR-0101`（メインエディタ＆プレビュー画面）の「3. 表示項目」において、エディタ本文の取得元が `API-0101.out.items[].content` と定義されているが、`API-0101`（ドキュメント一覧取得API）の出力契約（2.2）では `items` は `DocumentHeader`（`id`, `title`, `updated_at` のみ）であり、`content` が含まれていない。
このため、画面でドキュメントを選択した際に本文を取得・表示する契約が破綻している。

# 再現手順
1. `docs/20_basic-design/screen/SCR-0101-main-editor.md` の「3. 表示項目」を確認する（エディタ本文の取得元が `API-0101.out.items[].content` と記載）。
2. `docs/30_detail-design/api/API-0101-document-list.md` の「2.2 出力（正常）」を確認する（`items` に `content` が存在しない）。

# 原因
一覧取得APIの軽量化設計（メタデータのみ取得）を行った際、画面側でドキュメント選択時に本文データを取得するためのドキュメント詳細取得APIの設計および画面データバインディング契約の整合性確認が漏れていた。

# 恒久対策
> 恒久対策には「この指摘が二度と出ないようにするために、
> どのプロンプト / 規約 / 観点表を直すか」を必ず書く。

1. ドキュメント詳細取得API `API-0105 ドキュメント詳細取得API` (`GET /api/v1/documents/{document_id}`) を新規作成する。
2. `SCR-0101` の `calls_apis` に `API-0105` を追加し、表示項目の取得元を `API-0105.out.content` および `API-0105.out.title` に修正する。
3. 画面設計書作成プロンプト（`PRM-IMPL-SCR-001.md`）およびチェックツールに「画面の全入力・表示項目が呼出先APIのレスポンス定義（out）に過不足なく存在するか」の整合性検証観点を追加する。
