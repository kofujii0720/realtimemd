---
id: TBL-0001
name: ドキュメントテーブル
physical_name: documents
consumes: [UC-0101]
test_viewpoints: [VP-DATA-COMMON]
status: approved
version: 1
---

# TBL-0001 ドキュメントテーブル

## 1. 目的
Markdownドキュメントの基本情報および最新本文データを管理・永続化する。

## 2. カラム定義
| 物理名 | 論理名 | 型 | NULL | 既定値 | 制約 | 備考 |
|---|---|---|---|---|---|---|
| id | ドキュメントID | TEXT | NO | - | PRIMARY KEY | UUIDv4 |
| title | タイトル | TEXT | NO | '無題のドキュメント' | 最大255文字 | - |
| content | Markdown本文 | TEXT | NO | '' | 最大2MB | REQ-0003 |
| created_at | 作成日時 | TEXT | NO | - | ISO8601 UTC | REQ-0003 |
| updated_at | 更新日時 | TEXT | NO | - | ISO8601 UTC | REQ-0003 |

## 3. キー・インデックス
| 種別 | 対象カラム | 目的 |
|---|---|---|
| PRIMARY | id | レコードを一意識別するため |
| INDEX | updated_at DESC | ドキュメント更新順での一覧取得クエリ高速化のため |

## 4. 制約・不変条件
- `INV-1`: `updated_at` は `created_at` 以降の日時でなければならない。
- `INV-2`: `length(content)` は 2,097,152 バイト以下でなければならない (`REQ-0003`)。

## 5. データライフサイクル
- 登録: `API-0102` 呼び出し時
- 更新: `API-0103` 呼び出し時
- 削除: `API-0104` 呼び出し時 (物理削除)
- 保持期間: ユーザー削除操作まで無期限

## 6. 要確認事項
なし
