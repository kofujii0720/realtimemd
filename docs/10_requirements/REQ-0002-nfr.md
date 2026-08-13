---
id: REQ-0002
name: 非機能要件および品質閾値定義
test_viewpoints: [VP-API-COMMON, VP-SCR-COMMON]
status: approved
version: 1
---

# REQ-0002 非機能要件および品質閾値定義

## 1. 性能・応答性要件
- **リアルタイムプレビュー更新**: ユーザーのキー入力無操作後 100ms 以内に右ペインのプレビューがレンダリング完了すること。
- **ファイル保存・読み込み**: 1秒以内に完了すること。
- **PDFエクスポート生成**: 10ページ以内の文書において 3秒以内にPDFデータが生成完了すること。

## 2. 品質基準・センサー閾値 (L1〜L6)
- **L1 静的解析**: ESLint / Flake8 / mypy / tsc strict でエラー 0件。
- **L2 単体テスト**: Vitest / pytest 行カバレッジ 80% 以上、分岐カバレッジ 75% 以上。
- **L3 変異テスト**: Stryker / Mutmut スコア 60% 以上。
- **L6 設計書整合性**: `node scripts/check-docs.mjs` でエラー 0件。
