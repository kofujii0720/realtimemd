---
id: MSG-0001
name: メッセージ辞書
status: approved
version: 1
---

# MSG-0001 メッセージ辞書

全エラーおよび通知メッセージの定義正本。サーバーは messageKey のみを返却し、クライアントは本辞書を参照して描画する。

## 1. メッセージ一覧

| messageKey | 日本語メッセージ | 備考 |
|---|---|---|
| `error.document.notFound` | 指定されたドキュメントが見つかりません。 | E-0101-001, E-0103-001, E-0104-001 |
| `error.document.sizeExceeded` | ドキュメントのサイズ制限(2MB)を超過しています。 | E-0102-001, E-0103-002 |
| `error.document.titleRequired` | ドキュメントタイトルは必須です。 | E-0102-002, E-0103-003 |
| `error.export.pdfFailed` | PDFの生成処理に失敗しました。 | E-0301-001 |
| `error.common.systemError` | システムエラーが発生しました。時間をおいて再試行してください。 | E-0401-999 |
| `info.document.saved` | ドキュメントを保存しました。 | 成功通知 |
| `info.document.autoSaved` | 下書きを自動保存しました。 | 自動保存通知 |
| `label.status.empty` | ドキュメントがありません | 画面用表示ラベル |
