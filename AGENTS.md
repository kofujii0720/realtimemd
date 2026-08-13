# Realtime Markdown App — エージェント向け共通入口

このファイルは**目次**である。詳細・具体的なルールは各ファイルを参照すること。

## 1. システム概要と技術スタック
- **目的**: リアルタイムMarkdownレンダリング・プレビュー＆管理システム
- **フロントエンド**: React 18 / TypeScript / Vite / Vanilla CSS (CSS Modules) / remark / rehype / KaTeX / Mermaid
- **バックエンド**: Python 3.11+ / FastAPI / Pydantic (Strict) / SQLite / WeasyPrint (PDF生成)

## 2. 最初に読むもの
| 状況 | 読むファイル |
|---|---|
| 開発計画・TODO | `docs/50_plan/PLAN-0001-implementation-order.md` |
| 文書構造・対応マップ | `.agent/structures/doc-map.md` |
| コードと設計書の対応 | `.agent/structures/code-map.md` |
| ID採番ルール | `.agent/structures/id-scheme.md` |
| 事故防止規則 (必読) | `docs/10_requirements/REQ-0003-calc-rules.md` |

## 3. コマンド・スキル
- ★ `npm run check` または `node scripts/check-docs.mjs`: 設計書・コードの整合性チェック
- `/impl-api <API-ID>`: API設計書からサーバー実装
- `/impl-screen <SCR-ID>`: 画面設計書から画面実装
- `/write-tests <ID>`: 観点表から単体テスト作成（消化計画表を先に提示）
- `/write-e2e <SCR-ID>`: E2Eテスト作成（落ちる状態で終了）
- `/review-docs <ID...>`: 設計書整合性レビュー
- `/fix <エラー>`: 不具合の原因調査（分類報告のみ）
- `/extend-api <ID> <機能>`: 既存機能の差分拡張
- `/merge-parallel <ID...>`: 並列実装の集約
- `/ship <成果物名>`: 検証・コミット・プッシュ・PR

## 4. ガードレール・フック
- `scripts/hooks/block-docs-edit.sh`: 実装セッション中の `docs/` 直接改変を禁止 (`ALLOW_DOCS_EDIT=1` 環境変数でのみ変更許可)
- `scripts/hooks/stop-check-docs.sh`: ターン終了時に設計書整合性チェックを強制実行

## 5. ID体系 (リソース割当)
- `01`: ドキュメント・ファイル管理
- `02`: エディタ・リアルタイムプレビュー
- `03`: エクスポート (PDF/HTML)
- `04`: システム設定・共通

## 6. 禁止事項 (絶対厳守)
- 未確定事項を推測で埋めること（必ず `要確認事項` に記載）
- 設計書に書かれていない業務ルール・エラーコードの新設
- ID参照以外での文書間リンク（「〜を参照」等の文章参照）
- `usecases` / `domain` 層での直接的な `new Date()` 呼び出し
- 実装のついでに `docs/` を書き換えること（フックで自動拒否されます）
