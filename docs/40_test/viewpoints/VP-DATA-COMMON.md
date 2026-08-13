---
id: VP-DATA-COMMON
name: データベース共通テスト観点表
applies_to_doc_type: table-design
applies_when: "always"
derived_from:
  - section: "1. 目的"
    viewpoints: [VP-201]
  - section: "2. カラム定義"
    viewpoints: [VP-202]
  - section: "3. キー・インデックス"
    viewpoints: [VP-203]
  - section: "4. 制約・不変条件"
    viewpoints: [VP-204]
  - section: "5. データライフサイクル"
    viewpoints: [VP-205]
  - section: "6. 要確認事項"
    viewpoints: [VP-206]
coverage_rule: "100%"
status: approved
---

# VP-DATA-COMMON データベース共通テスト観点表

| ID | 観点 | 導出元 | 必須 | 生成ルール |
|---|---|---|---|---|
| VP-201 | テーブル定義意図確認 | 1. 目的 | △ | スキーマドキュメントの一致 |
| VP-202 | 型・NULL制約・初期値 | 2. カラム定義 | ○ | 不正型/NULL挿入エラーおよびデフォルト値割り当て検証 |
| VP-203 | 主キー・インデックス制約 | 3. キー・インデックス | ○ | 主キー重複エラー検証 |
| VP-204 | 不変条件 (INV) アサート | 4. 制約・不変条件 | ○ | アプリケーション層での不変条件違反拒否検証 |
| VP-205 | CRUDライフサイクル | 5. データライフサイクル | ○ | 登録・更新・物理/論理削除の挙動検証 |
| VP-206 | 要確認事項チェック | 6. 要確認事項 | ○ | 前提確認 |
