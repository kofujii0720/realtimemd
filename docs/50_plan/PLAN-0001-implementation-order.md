---
id: PLAN-0001
name: 実装順序・成果物一覧 (TODO)
status: approved
version: 1
---

# PLAN-0001 実装順序・成果物一覧 (TODO)

## 成果物一覧と実装順序

### マイルストーン 1: 開発基盤およびデータモデル構築
- [x] `#1` AGENTS.md, CLAUDE.md, GEMINI.md の配置
- [x] `#2` .agent/ 構造・規約・テンプレート群の配置
- [x] `#3` scripts/check-docs.mjs (L6センサー) の配置
- [x] `#4` docs/ 内設計書群（REQ, UC, TBL, MSG, SCR, API, VP）の配置
- [ ] `#5` SQLite スキーマ定義・マイグレーションスクリプト作成 (`db/migrations/001_initial.sql`)
- [ ] `#6` FastAPI 骨格アプリおよび Pydantic スキーマ層構築 (`app/`)

### マイルストーン 2: バックエンドAPI実装および単体テスト
- [ ] `#7` ドキュメントCRUD API実装 (`API-0101`〜`API-0104`)
- [ ] `#8` ドキュメントAPI単体テスト作成 (`tests/test_api_0101_0104.py`)
- [ ] `#9` PDFエクスポートAPI実装 (`API-0301`)
- [ ] `#10` エクスポートAPI単体テスト作成 (`tests/test_api_0301.py`)

### マイルストーン 3: フロントエンド実装およびE2Eテスト
- [ ] `#11` React + Vite + TypeScript エディタ＆リアルタイムプレビュー画面実装 (`SCR-0101`)
- [ ] `#12` エクスポート設定モーダル実装 (`SCR-0301`)
- [ ] `#13` Playwright E2Eテスト作成 (`tests/e2e/scr_0101_editor.spec.ts`)

### マイルストーン 4: CI・品質センサー検証・出荷
- [ ] `#14` GitHub Actions CI パイプライン構成 (`.github/workflows/ci.yml`)
- [ ] `#15` 全センサー (`npm run check`) 実行および PASS 確認
