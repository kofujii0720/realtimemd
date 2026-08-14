---
id: API-0104
name: ドキュメント削除API
method: DELETE
path: /api/v1/documents/{document_id}
layer: application
consumes: [UC-0101, TBL-0001, TBL-0002, MSG-0001, REQ-0003]
related_screens: [SCR-0101]
test_viewpoints: [VP-API-COMMON]
status: approved
version: 1
---

# API-0104 ドキュメント削除API

## 1. 目的
指定したドキュメントおよび関連する変更履歴データをデータベースから削除する。

## 2. インタフェース契約

### 2.1 入力
パスパラメータ:
- `document_id`: 削除対象ドキュメントID (UUID)

### 2.2 出力（正常）
レスポンスボディなし

HTTP ステータス: `204 No Content`

### 2.3 エラー
| コード | 条件 | HTTP | messageKey |
|---|---|---|---|
| E-0104-001 | 対象ドキュメントが存在しない | 404 | `MSG-0001.key.error.document.notFound` |
| E-0104-999 | 内部エラー | 500 | `MSG-0001.key.error.common.systemError` |

## 3. 事前条件 / 事後条件 / 不変条件
- 事前条件: `document_id` に一致するレコードが `TBL-0001` に存在すること。
- 事後条件: `TBL-0001` および関連する `TBL-0002` の該当レコードが削除されること。
- 不変条件: 削除対象外のドキュメントに影響を与えないこと。

## 4. 副作用
- DB更新: `TBL-0001` および `TBL-0002` DELETE

## 5. 非機能制約
- べき等性: あり

## 6. 処理順序の指定
指定なし（実装に委ねる）

## 7. 実装に委ねる範囲

## 8. 要確認事項
なし
