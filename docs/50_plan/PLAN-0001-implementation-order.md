---
id: PLAN-0001
name: 実装順序・成果物一覧
status: approved
version: 1
---

# PLAN-0001 実装順序・成果物一覧

## 成果物一覧と実装順序

### マイルストーン 1: 開発基盤およびドキュメント作成・プレビュー機能
- [x] `#1` AGENTS.md, CLAUDE.md, GEMINI.md の配置
- [x] `#2` .agent/ 構造・規約・テンプレート群の配置
- [x] `#3` scripts/check-docs.mjs (L6センサー) の配置
- [x] `#4` docs/ 内設計書群（REQ, UC, TBL, MSG, SCR, API, VP）の配置
- [ ] `#5` メイン画面E2Eテスト先行作成 (`/write-e2e SCR-0101`)
- [ ] `#6` ドキュメント作成API実装・単体テスト (`/impl-api API-0102`, `/write-tests API-0102`)
- [ ] `#7` ドキュメント更新API実装・単体テスト (`/impl-api API-0103`, `/write-tests API-0103`)
- [ ] `#8` プレビューHTMLレンダリングAPI実装・単体テスト (`/impl-api API-0201`, `/write-tests API-0201`)
- [ ] `#9` メインエディタ＆プレビュー画面実装・E2E通過 (`/impl-screen SCR-0101`)

### マイルストーン 2: 一覧取得・削除・エクスポート機能（並列化）
- [ ] `#10` ドキュメント一覧・詳細・削除API並列実装・集約 (`/impl-api API-0101`, `/impl-api API-0104`, `/impl-api API-0105`, `/merge-parallel`)
- [ ] `#11` ドキュメント一覧・詳細・削除API単体テスト並列作成 (`/write-tests API-0101`, `/write-tests API-0104`, `/write-tests API-0105`)
- [ ] `#12` PDFエクスポートAPI実装・単体テスト (`/impl-api API-0301`, `/write-tests API-0301`)
- [ ] `#13` エクスポート設定モーダル実装 (`/impl-screen SCR-0301`)
- [ ] `#14` メイン画面への一覧・削除・エクスポート導線追加 (`/extend-api SCR-0101`)
- [ ] `#15` エクスポートモーダルE2Eテスト作成・通過 (`/write-e2e SCR-0301`)

### マイルストーン 3: CI・全体品質検証・出荷
- [ ] `#16` GitHub Actions CI パイプライン構成 (`.github/workflows/ci.yml`)
- [ ] `#17` 全体設計整合性・全テスト一括検証 (`/review-docs`)
- [ ] `#18` 正式出荷 (`/ship`)
