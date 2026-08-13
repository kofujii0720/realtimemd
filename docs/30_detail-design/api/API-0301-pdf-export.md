---
id: API-0301
name: ドキュメントエクスポートAPI
method: POST
path: /api/v1/export
layer: application
consumes: [UC-0301]
related_screens: [SCR-0301]
test_viewpoints: [VP-API-COMMON]
status: approved
version: 1
---

# API-0301 ドキュメントエクスポートAPI

## 1. 目的
Markdown本文および出力オプション（PDF/HTML、用紙サイズ等）を受け取り、高精度なPDFバイナリまたはHTMLファイルを生成・返却する。

## 2. インタフェース契約

### 2.1 入力
| 項目 | 型 | 必須 | 値域・制約 | 備考 |
|---|---|---|---|---|
| content | String | YES | 最大2MB (`REQ-0003`) | Markdown本文 |
| format | String | YES | 'pdf' / 'html' | 出力形式 |
| paper_size | String | NO | 'A4' / 'Letter' | PDF出力時 (既定: 'A4') |

### 2.2 出力（正常）
型: Binary Stream (`application/pdf` または `text/html`)

HTTP ステータス: `200 OK`

### 2.3 エラー
| コード | 条件 | HTTP | messageKey |
|---|---|---|---|
| E-0301-001 | PDF生成処理失敗 | 500 | `MSG-0001.key.error.export.pdfFailed` |
| E-0301-002 | 不正な出力フォーマット指定 | 400 | `MSG-0001.key.error.common.systemError` |
| E-0301-999 | 内部エラー | 500 | `MSG-0001.key.error.common.systemError` |

## 3. 事前条件 / 事後条件 / 不変条件
- 事前条件: 特になし。
- 事後条件: DB状態変更なし。
- 不変条件: 特になし。

## 4. 副作用
なし

## 5. 非機能制約
- べき等性: あり
- 性能: 10ページ以内の文書で3秒以内生成 (`REQ-0002`)

## 6. 処理順序の指定
指定なし（実装に委ねる）

## 7. 実装に委ねる範囲
WeasyPrint 等のPDF生成ライブラリを利用する。

## 8. 要確認事項
なし
