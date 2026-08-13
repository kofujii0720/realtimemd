---
id: PLAN-0003
name: 逐次実行手順書 (Runbook)
status: approved
version: 1
---

# PLAN-0003 逐次実行手順書 (Runbook)

本ドキュメントは、**Realtime Markdown App** の開発開始から最終出荷までの完全な実行手順を定義する。
エージェントは各STEPを順番に実行し、各STEP完了毎に必ず `/ship` によるコミットと `/clear` によるコンテキストリセットを行うこと。

---

## 0. 基本運用ルール（全STEP共通）

1. **1成果物 = 1セッション**: 成果物1つの実装・テストが完了したら必ず `/ship` を実行し、直後に `/clear` を打ってコンテキストを初期化する。
2. **テスト先書き原則**: E2Eテストは実装前に作成し落ちる状態 (FAIL) で終了させる。単体テストは実装前に観点消化計画表を必ず最初に出力させる。
3. **設計書の変更禁止**: コード実装セッション中に `docs/` を直接書き換えてはならない（フック `block-docs-edit.sh` で強制ブロックされる）。
4. **不具合発生時の対処**: エラー発生時は直接コードを弄らず、まず `/fix <エラー>` で原因分類（A:実装バグ, B:テストバグ, C:設計欠陥）を行い、Cの場合は設計修正セッションへ切り替える。

---

## STEP 0: 設計書事前整合性チェック
開発を開始する前に、設計書の相互参照および構文が正常であることを確認する。

■ ターミナル
```bash
node scripts/check-docs.mjs
```
■ 終わったら
- エラー 0件で `exit status 0` になることを確認する。

■ 確認
- [ ] エラー件数が 0 件であること
- [ ] 参照切れ ID が存在しないこと

■ うまくいかないとき
- エラーメッセージに従い、該当設計書を修正する (`ALLOW_DOCS_EDIT=1` 環境変数が必要)。

---

## STEP 1: バックエンドディレクトリ構成＆DBマイグレーション作成 (`#5`)

■ ターミナル
```bash
mkdir -p app/api/v1 app/usecases app/repositories app/models app/schemas db/migrations
```
`db/migrations/001_initial.sql` に `TBL-0001` (documents) および `TBL-0002` (document_histories) の SQLite スキーマ定義を記述する。

■ セッションコマンド
```text
/ship "m1-initial-db-schema"
```
■ 終わったら
- 次のコマンドを実行してコンテキストをクリアする。
```text
/clear
```

■ 確認
- [ ] `db/migrations/001_initial.sql` が存在し、テーブル・インデックスが正しく記述されていること
- [ ] git commit & push が成功していること

---

## STEP 2: FastAPI サーバー骨格および共通設定の実装 (`#6`)

■ セッションコマンド
`app/main.py`, `app/core/config.py`, `app/core/messages.py` を作成し、FastAPI の骨格を初期化する。

■ 終わったら
```text
/ship "m1-fastapi-skeleton"
```
直後にコンテキストをリセットする。
```text
/clear
```

■ 確認
- [ ] FastAPI のルーティング基礎が設定されていること
- [ ] `MSG-0001` のメッセージキーが `app/core/messages.py` に正しく定義されていること

---

## STEP 3: フロントエンド (React + Vite + TypeScript) 環境構築 (`#6-2`)

■ ターミナル
```bash
npm create vite@latest . -- --template react-ts
npm install remark rehype remark-math rehype-katex mermaid lucide-react
npm install -D vitest @testing-library/react playwright
```

■ セッションコマンド
`src/` 配下の共通スタイル `src/styles/` および Vite 設定 (`vite.config.ts`) を調整する。

■ 終わったら
```text
/ship "m1-react-vite-setup"
```
直後にコンテキストをリセットする。
```text
/clear
```

■ 確認
- [ ] `npm run dev` が起動可能であること
- [ ] `tsconfig.json` で `strict: true` が設定されていること

---

## STEP 4: メインエディタ画面 E2E テストの事前作成 (`#13`)

■ セッションコマンド
```text
/write-e2e SCR-0101
```

■ ターミナル (テスト実行)
```bash
npx playwright test tests/e2e/scr_0101_editor.spec.ts
```

■ 終わったら
- **まだ画面が実装されていないため、テストが FAIL (落ちる) 状態であることを確認する。**
- テストを通すために画面実装を開始せず、落ちる状態のまま提出する。
```text
/ship "m2-e2e-scr-0101-initial"
```
直後にコンテキストをリセットする。
```text
/clear
```

■ 確認
- [ ] `tests/e2e/scr_0101_editor.spec.ts` が作成されていること
- [ ] テスト実行結果が FAIL であること

---

## STEP 5: ドキュメント一覧取得 API (`API-0101`) の実装 (`#7`, `#8`)

■ セッションコマンド
1. 単体テストの観点消化計画表を出力しテストを作成する。
```text
/write-tests VP-API-COMMON
```
2. APIを実装する。
```text
/impl-api API-0101
```

■ ターミnal (検証)
```bash
pytest tests/test_api_0101.py
```

■ 終わったら
```text
/ship "m2-impl-api-0101"
```
直後にコンテキストをリセットする。
```text
/clear
```

■ 確認
- [ ] `API-0101` の正常系・異常系単体テストが全件 PASS すること

■ うまくいかないとき
```text
/fix <エラーログ>
```
原因分類に従い対処する。

---

## STEP 6: ドキュメント新規作成 API (`API-0102`) の実装 (`#7`, `#8`)

■ セッションコマンド
```text
/write-tests VP-API-COMMON
```
```text
/impl-api API-0102
```

■ ターミナル
```bash
pytest tests/test_api_0102.py
```

■ 終わったら
```text
/ship "m2-impl-api-0102"
```
```text
/clear
```

---

## STEP 7: ドキュメント更新 API (`API-0103`) の実装 (`#7`, `#8`)

■ セッションコマンド
```text
/write-tests VP-API-COMMON
```
```text
/impl-api API-0103
```

■ ターミナル
```bash
pytest tests/test_api_0103.py
```

■ 終わったら
```text
/ship "m2-impl-api-0103"
```
```text
/clear
```

---

## STEP 8: ドキュメント削除 API (`API-0104`) の実装 (`#7`, `#8`)

■ セッションコマンド
```text
/write-tests VP-API-COMMON
```
```text
/impl-api API-0104
```

■ ターミナル
```bash
pytest tests/test_api_0104.py
```

■ 終わったら
```text
/ship "m2-impl-api-0104"
```
```text
/clear
```

---

## STEP 9: PDF エクスポート API (`API-0301`) の実装 (`#9`, `#10`)

■ セッションコマンド
```text
/write-tests VP-API-COMMON
```
```text
/impl-api API-0301
```

■ ターミナル
```bash
pytest tests/test_api_0301.py
```

■ 終わったら
```text
/ship "m2-impl-api-0301"
```
```text
/clear
```

---

## STEP 10: メインエディタ＆プレビュー画面 (`SCR-0101`) の実装 (`#11`)

■ セッションコマンド
```text
/impl-screen SCR-0101
```

■ 確認チェック
- [ ] `data-testid` が画面設計書通り付与されていること
- [ ] 読込中 / 0件 / 正常 / エラー の 4状態が実装されていること

■ 終わったら
```text
/ship "m3-impl-scr-0101"
```
```text
/clear
```

---

## STEP 11: エクスポート設定モーダル画面 (`SCR-0301`) の実装 (`#12`)

■ セッションコマンド
```text
/impl-screen SCR-0301
```

■ 終わったら
```text
/ship "m3-impl-scr-0301"
```
```text
/clear
```

---

## STEP 12: E2E テストの PASS 検証 (`#13`)

画面実装が完了したため、STEP 4 で作成して FAIL していた E2E テストを実行・検証する。

■ ターミナル
```bash
npx playwright test
```

■ 終わったら
- E2E テストが全件 PASS することを確認する。
```text
/ship "m3-e2e-pass-verification"
```
```text
/clear
```

■ うまくいかないとき
- エラーログを確認し、`/fix <エラー>` で不具合分類を行う。実装のバグであれば画面/APIコードを修正する。

---

## STEP 13: 最終全品質センサーチェックおよび出荷 (`#14`, `#15`)

リポジトリ全体に対する最終品質チェックを実行する。

■ ターミナル
```bash
node scripts/check-docs.mjs
npm run check
```

■ セッションコマンド
```text
/ship "v1.0.0-release"
```

■ 完了
- 全ての CI チェックが緑 (PASS) であることを確認し、Pull Request をマージして開発完了とする。
