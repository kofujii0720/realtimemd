---
id: PRM-TST-E2E-001
name: E2Eテスト作成プロンプト正本
phase: test
activity: 画面設計書から Playwright E2E テストを作成する
inputs:
  - path: docs/20_basic-design/screen/SCR-XXXX-*.md
    required: true
rules:
  - .agent/rules/testing.md
version: 1
---

# 手順

## Step 1: コンテキスト収集
- 画面設計書 (`SCR-XXXX`) を読み込み、`data-testid` および必須シナリオ (2回連続操作、中断・再開、空データ等) を確認する。

## Step 2: E2E テスト記述
- Playwright spec ファイルを作成する。
- 要素選択には `data-testid` のみを使用する。

## Step 3: テスト実行
- 未実装状態のためテストが FAIL することを確認し、落ちる状態でセッションを完結させる。テストを通すために画面コードの実装を開始しないこと。
