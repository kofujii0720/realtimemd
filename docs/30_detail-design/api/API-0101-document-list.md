---
id: API-0101
name: ドキュメント一覧取得API
method: GET
path: /api/v1/documents
layer: application
consumes: [UC-0101, TBL-0001]
related_screens: [SCR-0101]
test_viewpoints: [VP-API-COMMON]
status: approved
version: 1
---

# API-0101 ドキュメント一覧取得API

## 1. 目的
登録されている全ドキュメントのメタデータ一覧（ID, タイトル, 更新日時）を更新日時昇降順で取得する。

## 2. インタフェース契約

### 2.1 入力
| 項目 | 型 | 必須 | 値域・制約 | 備考 |
|---|---|---|---|---|
| limit | Integer | NO | 1〜100 | デフォルト50 |
| offset | Integer | NO | 0以上 | デフォルト0 |

### 2.2 出力（正常）
| 項目 | 型 | 説明 |
|---|---|---|
| total | Integer | 登録総件数 |
| items | Array[DocumentHeader] | ドキュメントメタデータ一覧 |
| items[].id | String | ドキュメントID (UUID) |
| items[].title | String | タイトル |
| items[].updated_at | String | 最終更新日時 (ISO8601 UTC) |

HTTP ステータス: `200 OK`

### 2.3 エラー
| コード | 条件 | HTTP | messageKey |
|---|---|---|---|
| E-0101-001 | クエリパラメータ制約違反 | 400 | `MSG-0001.key.error.common.systemError` |
| E-0101-999 | 内部エラー | 500 | `MSG-0001.key.error.common.systemError` |

## 3. 事前条件 / 事後条件 / 不変条件
- 事前条件: 特になし。
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
