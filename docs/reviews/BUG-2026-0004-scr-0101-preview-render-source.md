---
schema_version: 1
id: BUG-2026-0004
detected_phase: REVIEW
detected_at: 2026-08-19T22:52:29+09:00
detected_by: agent
target_artifact: SCR-0101
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
`UC-0201` ではクライアント側の remark/rehype パイプラインによりリアルタイム変換（100msデバウンス）を行うと規定されており、`API-0201` はサーバー側での解析が必要な場合の補助APIであるにもかかわらず、`SCR-0101` の「3. 表示項目」においてプレビューペインの取得元が `API-0201.out.html_content` 固定として記載されている。
このため、画面レンダリングの責務・データフローがユースケースおよびAPI設計と不整合になっている。

# 再現手順
1. `docs/20_basic-design/screen/SCR-0101-main-editor.md` の「3. 表示項目」を確認する（プレビューペインの取得元が `API-0201.out.html_content` と記載）。
2. `docs/10_requirements/uc/UC-0201-editor-preview.md` の「3. 基本フロー」を確認する（クライアント側 remark/rehype でリアルタイム変換と規定）。
3. `docs/30_detail-design/api/API-0201-preview-render.md` の「1. 目的」を確認する（クライアントJSパーサーの補完用と規定）。

# 原因
画面設計書作成時に、プレビュー領域のデータ取得元としてサーバーAPI（`API-0201`）のみを機械的に割り当て、クライアントサイドレンダリングとの主従関係を明記しなかった。

# 恒久対策
> 恒久対策には「この指摘が二度と出ないようにするために、
> どのプロンプト / 規約 / 観点表を直すか」を必ず書く。

1. `SCR-0101` の「3. 表示項目」のプレビューペイン取得元を「フロントエンドパーサー変換結果（補完時: `API-0201.out.html_content`）」と修正する。
2. 画面設計書作成プロンプト（`PRM-IMPL-SCR-001.md`）において、クライアント処理とサーバーAPI呼び出しの責務境界を明確に記述するルールを追加する。
