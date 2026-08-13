---
id: VP-SCR-COMMON
name: 画面共通テスト観点表
applies_to_doc_type: screen-design
applies_when: "always"
derived_from:
  - section: "1. 目的"
    viewpoints: [VP-101]
  - section: "2. 画面構成"
    viewpoints: [VP-102]
  - section: "3. 表示項目"
    viewpoints: [VP-103]
  - section: "4. 入力項目"
    viewpoints: [VP-104]
  - section: "5. 操作と遷移"
    viewpoints: [VP-105]
  - section: "6. 状態と表示の対応"
    viewpoints: [VP-106]
  - section: "7. 非機能・アクセシビリティ"
    viewpoints: [VP-107]
  - section: "8. 要確認事項"
    viewpoints: [VP-108]
coverage_rule: "100%"
status: approved
---

# VP-SCR-COMMON 画面共通テスト観点表

| ID | 観点 | 導出元 | 必須 | 生成ルール |
|---|---|---|---|---|
| VP-101 | 画面表示・ルーティング | 1. 目的 | ○ | 指定ルートアクセスの表示テスト |
| VP-102 | コンポーネント配置 | 2. 画面構成 | ○ | 領域ごとのDOMツリー存在確認 |
| VP-103 | 表示データマッピング | 3. 表示項目 | ○ | API応答から data-testid 要素への描画検証 |
| VP-104 | フォーム入力・バリデーション | 4. 入力項目 | ○ | 必須・型・制限文字数の入力検証 |
| VP-105 | 操作・API呼出・画面遷移 | 5. 操作と遷移 | ○ | ボタンクリック時のAPI呼び出しおよび成功/失敗時の遷移 |
| VP-106 | 画面4状態（読込中/0件/正常/エラー） | 6. 状態と表示の対応 | ○ | 4状態全てのレンダリングアサート |
| VP-107 | キーボード・レスポンシブ | 7. 非機能・アクセシビリティ | △ | ショートカットキーおよびリサイズ時の描画テスト |
| VP-108 | 要確認事項チェック | 8. 要確認事項 | ○ | 前提条件確認 |
