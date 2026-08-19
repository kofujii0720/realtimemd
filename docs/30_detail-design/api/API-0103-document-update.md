---
id: API-0103
name: ドキュメント更新API
method: PUT
path: /api/v1/documents/{document_id}
layer: application
consumes: [UC-0101, TBL-0001, TBL-0002, MSG-0001, REQ-0003]
related_screens: [SCR-0101]
test_viewpoints: [VP-API-COMMON]
status: approved
version: 1
---

# API-0103 ドキュメント更新API

## 1. 目的
指定したドキュメントのタイトル・本文を更新する。明示保存フラグ (`is_explicit_save=true`) 時は変更履歴 (`TBL-0002`) にレコードを追加する。

## 2. インタフェース契約

### 2.1 入力
パスパラメータ:
- `document_id`: ドキュメントID (UUID)

ボディ:
| 項目 | 型 | 必須 | 値域・制約 | 備考 |
|---|---|---|---|---|
| title | String | YES | 1〜255文字 | タイトル |
| content | String | YES | 最大2MB (`REQ-0003`) | 本文 |
| is_explicit_save | Boolean | NO | true / false | デフォルト false |

### 2.2 出力（正常）
| 項目 | 型 | 説明 |
|---|---|---|
| id | String | ドキュメントID |
| title | String | 更新後タイトル |
| content | String | 更新後本文 |
| updated_at | String | 更新日時 (ISO8601 UTC) |

HTTP ステータス: `200 OK`

### 2.3 エラー
| コード | 条件 | HTTP | messageKey |
|---|---|---|---|
| E-0103-001 | 対象ドキュメントが存在しない | 404 | `MSG-0001.key.error.document.notFound` |
| E-0103-002 | 本文サイズ制限(2MB)超過 | 400 | `MSG-0001.key.error.document.sizeExceeded` |
| E-0103-003 | タイトル未入力・空 | 400 | `MSG-0001.key.error.document.titleRequired` |
| E-0103-004 | タイトル文字数制限(255文字)超過 | 400 | `MSG-0001.key.error.document.titleTooLong` |
| E-0103-999 | 内部エラー | 500 | `MSG-0001.key.error.common.systemError` |

## 3. 事前条件 / 事後条件 / 不変条件
- 事前条件: `document_id` に一致するレコードが `TBL-0001` に存在すること。
- 事後条件: `TBL-0001.col.updated_at` が現在時刻に更新されること。`is_explicit_save=true` の場合、`TBL-0002` に履歴が追加されること。
- 不变条件: `TBL-0001.col.created_at` は変更されないこと。

## 4. 副作用
- DB更新: `TBL-0001` UPDATE, (`TBL-0002` INSERT)

## 5. 非機能制約
- べき等性: あり

## 6. 処理順序の指定
理由: 明示保存時の履歴整合性を保証するため、`TBL-0001` の更新と `TBL-0002` への履歴追加は同一トランザクション内で行うこと。

## 7. 実装に委ねる範囲

## 8. 要確認事項
なし
