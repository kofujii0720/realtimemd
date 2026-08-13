# 命名規約および用語辞書 (naming.md)

本プロジェクトで使用する標準用語と命名ルールの定義。

## 1. 用語辞書 (表記の統一)

| 使う表記 | 使わない表記 | 意味 |
|---|---|---|
| document | file, md_file, text, article | Markdownドキュメント |
| content | body, text_content, markdown_text | ドキュメントの本文テキスト |
| history | version, log, backup | ドキュメントの変更履歴 |
| export | output, convert, download | PDF/HTML等への変換・出力 |
| autoSave | auto_backup, backgroundSave | 自動下書き保存 |

## 2. 変数・ファイル命名規則
- **DB (SQLite)**: snake_case (`created_at`, `document_id`)
- **API (FastAPI JSON / Pydantic)**: camelCase (Python Pydantic側で alias/by_alias を設定) または snake_case
- **TypeScript / React**: camelCase (`documentId`), コンポーネントは PascalCase (`EditorPanel.tsx`)
- **設計書**: ID-ケバブケース名 (`API-0101-document-create.md`)
