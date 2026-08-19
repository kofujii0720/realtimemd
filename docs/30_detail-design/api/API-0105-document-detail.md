---
id: API-0105
name: ドキュメント詳細取得API
method: GET
path: /api/v1/documents/{document_id}
layer: application
consumes: [UC-0101, TBL-0001, MSG-0001, REQ-0003]
related_screens: [SCR-0101]
test_viewpoints: [VP-API-COMMON]
status: approved
version: 1
---

# API-0105 ドキュメント詳細取得API

## 1. 目的
指定したドキュメントIDの詳細データ（ID, タイトル, 本文, 作成日時, 最終更新日時）を取得する。

## 2. インタフェース契約

### 2.1 入力
パスパラメータ:
- `document_id`: 取得対象ドキュメントID (UUID)

### 2.2 出力（正常）
| 項目 | 型 | 説明 |
|---|---|---|
| id | String | ドキュメントID (UUID) |
| title | String | タイトル |
| content | String | 本文データ |
| created_at | String | 作成日時 (ISO8601 UTC) |
| updated_at | String | 最終更新日時 (ISO8601 UTC) |

HTTP ステータス: `200 OK`

### 2.3 エラー
| コード | 条件 | HTTP | messageKey |
|---|---|---|---|
| E-0105-001 | 対象ドキュメントが存在しない | 404 | `MSG-0001.key.error.document.notFound` |
| E-0105-999 | 内部エラー | 500 | `MSG-0001.key.error.common.systemError` |

## 3. 事前条件 / 事後条件 / 不変条件
- 事前条件: `document_id` に一致するレコードが `TBL-0001` に存在すること。
- 事後条件: DBの状態変更なし。
- 不変条件: 特になし。

## 4. 副作用
なし

## 5. 非機能制約
- べき等性: あり
- 応答性能: 200ms 以内

## 6. 処理順序の指定
指定なし（実装に委ねる）

## 7. 実装に委ねる範囲
標準的な FastAPI リポジトリパターンに従う。

## 8. 要確認事項
なし
