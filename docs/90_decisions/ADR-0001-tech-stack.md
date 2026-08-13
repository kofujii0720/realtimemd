---
id: ADR-0001
name: フロントエンド・バックエンド技術スタックの選定
status: accepted
date: 2026-08-13
consumes: [REQ-0001, REQ-0002]
---

# ADR-0001 フロントエンド・バックエンド技術スタックの選定

## 状況
Realtime Markdown アプリの構築において、ハーネス適合性（厳格な型チェック、コンポーネント分離、単体/E2Eテスト容易性、高速なリアルタイムプレビュー）を満たす技術スタックを選定する必要があった。

## 決定
フロントエンドに **React 18 + Vite + TypeScript (Strict) + CSS Modules**、バックエンドに **Python 3.11+ + FastAPI + Pydantic (Strict) + SQLite** を採用する。

## 理由
1. **フロントエンド (React + Vite + remark/rehype)**:
   - クライアントサイドでのデバウンス100msによるリアルタイムHTML/Mermaid/KaTeX表示が最も高速かつ安定して実現できる。
   - Vitest および Playwright との親和性が高く、`data-testid` を用いた画面状態検証が容易である。
2. **バックエンド (FastAPI + Pydantic + SQLite)**:
   - 入出力スキーマが Pydantic により厳格に固定でき、設計書 `API-XXXX` との 1:1 対応が容易である。
   - WeasyPrint や Playwright 連携による高精度な PDF エクスポート処理をサーバー側で確実に行える。

## 帰結
- **良い点**:
  - クライアントサイドプレビューの高速化とサーバーサイド高精度PDFエクスポートの両立。
  - テスト容易性と機械検証可能性の最大化。
- **悪い点**:
  - Python環境とNode.js環境の両方のセットアップが必要。
  - 緩和策: 開発手順およびビルド手順を `PLAN-0003` に一意にドキュメント化する。

## 関連
- REQ-0001, REQ-0002
