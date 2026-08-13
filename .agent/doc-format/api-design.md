---
id: API-XXXX
name: <APIの名前>
method: <GET|POST|PUT|PATCH|DELETE>
path: /api/v1/...
layer: application
consumes: [UC-XXXX, TBL-XXXX]
related_screens: [SCR-XXXX]
test_viewpoints: [VP-...]
status: draft
version: 1
---

# API-XXXX <APIの名前>

## 1. 目的

## 2. インタフェース契約

### 2.1 入力
| 項目 | 型 | 必須 | 値域・制約 | 備考 |
|---|---|---|---|---|

### 2.2 出力（正常）
| 項目 | 型 | 説明 |
|---|---|---|

### 2.3 エラー
| コード | 条件 | HTTP | messageKey |
|---|---|---|---|

## 3. 事前条件 / 事後条件 / 不変条件
- 事前条件：
- 事後条件：
- 不变条件：

## 4. 副作用
- DB更新：
- 外部連携：
- 通知：

## 5. 非機能制約
- トランザクション境界：
- べき等性：
- 性能：
- 監査ログ：

## 6. 処理順序の指定
指定なし（実装に委ねる）

## 7. 実装に委ねる範囲

## 8. 要確認事項
なし
