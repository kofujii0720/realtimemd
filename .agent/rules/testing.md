# テスト規約 (testing.md)

## 1. 単体テスト方針 (Vitest / pytest)
- デトロイト派（古典派）。モックは外部I/O（ファイルシステム・HTTP・時刻等）のみに留める。
- テストケースは必ずテスト観点表 (`VP-XXXX`) から導出する。
- テスト名には必ず観点IDを含める (例: `test_[VP-001]_valid_document_create`).

## 2. 画面・E2Eテスト方針 (Playwright)
- 要素の選択には `data-testid` のみを使用する。
- 画面設計書 (`SCR-XXXX`) の4状態（読込中・0件・正常・エラー）の動作検証を含めること。
