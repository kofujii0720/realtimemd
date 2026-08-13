---
id: REQ-0001
name: Realtime Markdown アプリ 要件定義概要
test_viewpoints: [VP-API-COMMON, VP-SCR-COMMON]
status: approved
version: 1
---

# REQ-0001 Realtime Markdown アプリ 要件定義概要

## 1. 目的とビジョン
ユーザーがブラウザ上で快適にMarkdown文書を作成・編集し、リアルタイムにレンダリング（HTML, Mermaid図表, KaTeX数式）結果を確認しながら、FastAPIバックエンドを介して安全なファイル永続化および高精度なPDFエクスポートを行える環境を提供する。

## 2. コア機能範囲
- **デュアルペインエディタ**: 左ペインでMarkdown編集、右ペインでリアルタイムHTML/Mermaid/KaTeX表示。
- **ファイル・ドキュメント管理**: FastAPI + SQLite によるドキュメントCRUD、下書き自動保存、変更履歴保持。
- **PDF/HTMLエクスポート**: FastAPI バックエンド (WeasyPrint等) を用いたスタイル崩れのないPDF高精度出力。

## 3. 業務領域・リソース定義 (ID体系)
- `01`: ドキュメント・ファイル管理 (`UC-0101`, `SCR-0101`, `API-0101`〜`API-0104`, `TBL-0001`〜`TBL-0002`)
- `02`: エディタ・リアルタイムプレビュー (`UC-0201`, `API-0201`)
- `03`: エクスポート (PDF/HTML) (`UC-0301`, `SCR-0301`, `API-0301`)
- `04`: システム設定・共通 (`MSG-0001`, `REQ-0002`〜`0003`)
