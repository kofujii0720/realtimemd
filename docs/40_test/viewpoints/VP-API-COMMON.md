---
id: VP-API-COMMON
name: API共通テスト観点表
applies_to_doc_type: api-design
applies_when: "always"
derived_from:
  - section: "2.1 入力"
    viewpoints: [VP-001, VP-002]
  - section: "2.2 出力（正常）"
    viewpoints: [VP-003]
  - section: "2.3 エラー"
    viewpoints: [VP-004]
  - section: "3. 事前条件 / 事後条件 / 不変条件"
    viewpoints: [VP-005]
  - section: "4. 副作用"
    viewpoints: [VP-006]
  - section: "5. 非機能制約"
    viewpoints: [VP-007]
  - section: "6. 処理順序の指定"
    viewpoints: [VP-008]
  - section: "7. 実装に委ねる範囲"
    viewpoints: [VP-009]
  - section: "8. 要確認事項"
    viewpoints: [VP-010]
coverage_rule: "100%"
status: approved
---

# VP-API-COMMON API共通テスト観点表

| ID | 観点 | 導出元 | 必須 | 生成ルール |
|---|---|---|---|---|
| VP-001 | 入力必須・型チェック | 2.1 入力 | ○ | 必須項目の欠損および型不一致テスト |
| VP-002 | 境界値・制約チェック | 2.1 入力 | ○ | 下限-1, 下限, 上限, 上限+1 の4点テスト |
| VP-003 | 正常レスポンス検証 | 2.2 出力（正常） | ○ | HTTP 200/201 ステータスとレスポンスボディ構造検証 |
| VP-004 | 定義済みエラー発生検証 | 2.3 エラー | ○ | 各エラーコード条件の発生とレスポンスコード検証 |
| VP-005 | 事前・事後条件・不変条件検証 | 3. 事前条件 / 事後条件 / 不変条件 | ○ | 事後条件のDB更新と不変条件の不変アサート |
| VP-006 | 副作用検証 | 4. 副作用 | ○ | DB更新・通知等の副作用発生確認 |
| VP-007 | べき等性・性能検証 | 5. 非機能制約 | △ | 同一リクエストの複数回実行挙動確認 |
| VP-008 | 処理順序の保証検証 | 6. 処理順序の指定 | ○ | 指定された順序通りのトランザクション実行 |
| VP-009 | 実装自由度範囲の確認 | 7. 実装に委ねる範囲 | △ | アーキテクチャ規約遵守 |
| VP-010 | 未決定事項なしの確認 | 8. 要確認事項 | ○ | テスト実行時の前提不整合ゼロ |
