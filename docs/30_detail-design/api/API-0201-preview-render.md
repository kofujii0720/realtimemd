---
id: API-0201
name: プレビューレンダリング補助API
method: POST
path: /api/v1/preview/render
layer: application
consumes: [UC-0201, MSG-0001, REQ-0003]
related_screens: [SCR-0101]
test_viewpoints: [VP-API-COMMON]
status: approved
version: 1
---

# API-0201 プレビューレンダリング補助API

## 1. 目的
（フロントエンドのJSパーサーの補完用として）サーバー側での高度なMarkdown/HTML解析・検証が必要な場合に変換後のHTML文字列を返却する。

## 2. インタフェース契約

### 2.1 入力
| 項目 | 型 | 必須 | 値域・制約 | 備考 |
|---|---|---|---|---|
| content | String | YES | 最大2MB (`REQ-0003`) | 変換対象Markdown |

### 2.2 出力（正常）
| 項目 | 型 | 説明 |
|---|---|---|
| html_content | String | 変換後安全なHTML文字列 |

HTTP ステータス: `200 OK`

### 2.3 エラー
| コード | 条件 | HTTP | messageKey |
|---|---|---|---|
| E-0201-001 | 入力サイズ制限(2MB)超過 | 400 | `MSG-0001.key.error.document.sizeExceeded` |
| E-0201-999 | 内部エラー | 500 | `MSG-0001.key.error.common.systemError` |

## 3. 事前条件 / 事後条件 / 不変条件
- 事前条件: 特になし。
- 事後条件: DB状態変更なし。
- 不変条件: 特になし。

## 4. 副作用
なし

## 5. 非機能制約
- べき等性: あり

## 6. 処理順序の指定
指定なし（実装に委ねる）

## 7. 実装に委ねる範囲

## 8. 要確認事項
なし
