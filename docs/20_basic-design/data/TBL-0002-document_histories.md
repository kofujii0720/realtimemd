---
id: TBL-0002
name: ドキュメント変更履歴テーブル
physical_name: document_histories
consumes: [UC-0101]
test_viewpoints: [VP-DATA-COMMON]
status: approved
version: 1
---

# TBL-0002 ドキュメント変更履歴テーブル

## 1. 目的
明示保存操作時にドキュメントのスナップショット（スナップショット本文およびバージョン情報）を履歴として記録する。

## 2. カラム定義
| 物理名 | 論理名 | 型 | NULL | 既定値 | 制約 | 備考 |
|---|---|---|---|---|---|---|
| id | 履歴ID | TEXT | NO | - | PRIMARY KEY | UUIDv4 |
| document_id | ドキュメントID | TEXT | NO | - | FOREIGN KEY (`TBL-0001.col.id`) | 外部キー |
| version_no | バージョン番号 | INTEGER | NO | 1 | - | ドキュメント毎の連番 |
| content | バックアップ本文 | TEXT | NO | '' | 最大2MB | REQ-0003 |
| saved_at | 保存日時 | TEXT | NO | - | ISO8601 UTC | REQ-0003 |

## 3. キー・インデックス
| 種別 | 対象カラム | 目的 |
|---|---|---|
| PRIMARY | id | レコード一意識別のため |
| INDEX | document_id, version_no DESC | 対象ドキュメントの履歴取得のため |

## 4. 制約・不変条件
- `INV-1`: `document_id` は `TBL-0001` に存在するレコードの `id` でなければならない。

## 5. データライフサイクル
- 登録: `API-0103` での明示保存時
- 削除: 親ドキュメント (`TBL-0001`) 削除に伴う CASCADE 物理削除

## 6. 要確認事項
なし
