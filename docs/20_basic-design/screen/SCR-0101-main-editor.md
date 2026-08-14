---
id: SCR-0101
name: メインエディタ＆プレビュー画面
route: /
consumes: [UC-0101, UC-0201, MSG-0001, REQ-0003]
calls_apis: [API-0101, API-0102, API-0103, API-0104, API-0201]
test_viewpoints: [VP-SCR-COMMON]
status: approved
version: 1
---

# SCR-0101 メインエディタ＆プレビュー画面

## 1. 目的
Markdownドキュメントの作成・選択・編集、およびリアルタイムプレビューの確認を行うメイン画面。

## 2. 画面構成
- サイドバー領域: ドキュメント一覧リスト、新規作成ボタン
- ヘッダー領域: タイトル入力欄、手動保存ボタン、エクスポートボタン、削除ボタン
- エディタ領域 (左ペイン): Markdownテキストエディタ
- プレビュー領域 (右ペイン): リアルタイムレンダリングペイン (HTML / Mermaid / KaTeX)

## 3. 表示項目
| 項目名 | data-testid | 型 | 取得元 | 表示条件 | 書式 |
|---|---|---|---|---|---|
| ドキュメント一覧 | doc-list | Array | `API-0101.out.items` | 常時 | タイトル一覧 |
| タイトル入力 | doc-title-input | String | `API-0101.out.items[].title` | ドキュメント選択時 | テキスト |
| エディタ本文 | doc-editor-textarea | String | `API-0101.out.items[].content` | ドキュメント選択時 | Markdownテキスト |
| プレビューペイン | doc-preview-pane | HTML | `API-0201.out.html_content` | ドキュメント選択時 | HTML/SVGレンダリング |
| エラー表示 | error-banner | String | `MSG-0001` | エラー発生時 | アラート表示 |

## 4. 入力項目
| 項目名 | data-testid | 型 | 必須 | 制約 | 初期値 |
|---|---|---|---|---|---|
| タイトル | doc-title-input | String | YES | 最大255文字 | '無題のドキュメント' |
| 本文 | doc-editor-textarea | String | NO | 最大2MB | '' |

## 5. 操作と遷移
| 操作 | data-testid | 前提条件 | 呼び出すAPI | 成功時 | 失敗時 |
|---|---|---|---|---|---|
| 新規作成ボタン | btn-create-doc | なし | `API-0102` | 新規ドキュメントを選択 | `MSG-0001.key.error.common.systemError` |
| 保存ボタン | btn-save-doc | ドキュメント選択時 | `API-0103` | `MSG-0001.key.info.document.saved` / `MSG-0001.key.info.document.autoSaved` 表示 | `MSG-0001.key.error.document.sizeExceeded` 等 |
| エクスポートボタン | btn-open-export | ドキュメント選択時 | なし | SCR-0301 モーダルを開く | なし |
| 削除ボタン | btn-delete-doc | ドキュメント選択時 | `API-0104` | 一覧更新、先頭を選択 | `MSG-0001.key.error.document.notFound` |

## 6. 状態と表示の対応
| 状態 | 表示 |
|---|---|
| 読込中 | ドキュメント一覧およびプレビューペインにスピナーインジケータ (`doc-loading-spinner`) を表示する。 |
| 0件 | 「ドキュメントがありません」 (`MSG-0001.key.label.status.empty`) メッセージおよび「新規作成」導線ボタンを表示する。 |
| 正常 | ドキュメント一覧、選択ドキュメントのタイトル、エディタ、およびプレビューペインを表示する。 |
| エラー | 画面上部にエラーメッセージバナー (`error-banner`) を赤字で表示する。 |

## 7. 非機能・アクセシビリティ
- キーボードショートカット: Ctrl+S / Cmd+S で保存操作を実行する。
- レスポンシブ: 画面幅800px以下ではエディタ/プレビューのタブ切替方式にフォールバックする。

## 8. 要確認事項
なし
