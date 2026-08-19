---
id: API-0102
name: ドキュメント新規作成API
method: POST
path: /api/v1/documents
layer: application
consumes: [UC-0101, TBL-0001, MSG-0001, REQ-0003]
related_screens: [SCR-0101]
test_viewpoints: [VP-API-COMMON]
status: approved
version: 1
---

# API-0102 ドキュメント新規作成API

## 1. 目的
新しい空のMarkdownドキュメントレコードを作成し、初期化されたドキュメント情報を返却する。

## 2. インタフェース契約

### 2.1 入力
| 項目 | 型 | 必須 | 値域・制約 | 備考 |
|---|---|---|---|---|
| title | String | NO | 最大255文字 | 未指定時 '無題のドキュメント' |
| content | String | NO | 最大2MB (`REQ-0003`) | 初期値 '' |

### 2.2 出力（正常）
| 項目 | 型 | 説明 |
|---|---|---|
| id | String | 発行されたドキュメントID (UUIDv4) |
| title | String | 設定されたタイトル |
| content | String | 本文データ |
| created_at | String | 作成日時 (ISO8601 UTC) |
| updated_at | String | 更新日時 (ISO8601 UTC) |

HTTP ステータス: `201 Created`

### 2.3 エラー
| コード | 条件 | HTTP | messageKey |
|---|---|---|---|
| E-0102-001 | 本文サイズ制限(2MB)超過 | 400 | `MSG-0001.key.error.document.sizeExceeded` |
| E-0102-002 | タイトル文字数制限(255文字)超過 | 400 | `MSG-0001.key.error.document.titleTooLong` |
| E-0102-999 | 内部エラー | 500 | `MSG-0001.key.error.common.systemError` |

## 3. 事前条件 / 事後条件 / 不変条件
- 事前条件: 特になし。
- 事後条件: `TBL-0001` に新規レコードが1件追加されること。
- 不変条件: `created_at` と `updated_at` は同値であること。

## 4. 副作用
- DB更新: `TBL-0001` への INSERT

## 5. 非機能制約
- べき等性: なし (POSTリクエスト毎に新規作成)

## 6. 処理順序の指定
指定なし（実装に委ねる）

## 7. 実装に委ねる範囲

## 8. 要確認事項
なし
