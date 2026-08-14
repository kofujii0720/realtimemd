---
id: PLAN-0003
name: 実行手順書
consumes: [PLAN-0001, PLAN-0002]
status: approved
version: 1
---

# PLAN-0003 実行手順書

**上から順に実行する。** 各 STEP は「打つもの → 終わったら → 確認」の3点セット。
Agent への指示は**自然文プロンプトを使わず、すべてスラッシュコマンド（スキル）**を入力する。
`■ ターミナル` はシェルに、`■ Agent` は Claude Code / Antigravity のセッション内に入力する。

## この手順書の読み方

```
### STEP n  やること
■ ターミナル        ← シェルに貼り付ける
■ Agent             ← スラッシュコマンド（スキル）を打つ
■ 終わったら        ← /ship で自動検証・コミット・プッシュ・PR作成
■ 確認              ← 次へ進む前のチェック
■ うまくいかないとき ← 失敗時の対処（/fix 等）
```

## 全体像

| フェーズ | STEP | 内容 | 目安 |
|---|---|---|---|
| 準備 | 1〜5 | リポジトリと起動確認・スキル認識検証 | 30分 |
| M1 | 6〜18 | ドキュメント作成・更新・リアルタイムプレビュー（直列） | 半日〜1日 |
| M2 | 19〜29 | 一覧取得・削除・エクスポート（**並列化デビュー**） | 半日〜1日 |
| M3 | 30〜33 | CI整備・全体品質検証・出荷 | 2時間 |

**M2 まででドキュメント管理・リアルタイムプレビュー・PDFエクスポートアプリとして完全に動作する。**

---

## 押さえておく3つのルール

### ルール1：成果物の確定と push / PR 作成は `/ship` で行う

**`/ship` を実行した時点で、整合性チェック・テスト検証・commit・push・PR作成が完了する。**
手動でのコミットや `gh` コマンドによるPR作成は不要。

`/ship` は次を自動で行う。

1. `node scripts/check-docs.mjs` (L6センサー) および単体・E2Eテストを実行し、落ちていたら中止する
2. 差分を確認し、意図しないファイルが混ざっていないか点検する
3. コミットメッセージを作成してコミットする
4. リモートリポジトリへ `git push` し、PRを作成する

**`/ship` を打たずに次の STEP へ進まないこと。** 手元にしかない状態を残さない。

作業を中断するときは、STEP の途中でも次を打つ。

```
/ship "作業途中: <何をしていたか>"
```

テストが落ちていて `/ship` が使えない場合のみ、手動で退避する。

```bash
git add -A && git commit -m "wip: 作業途中" --no-verify && git push
```

### ルール2：1 STEP = 1セッション

**STEP が1つ終わったら必ず `/clear` を打つ。**

コンテキストが積み上がると、Agent は前の作業の前提を引きずり、
設計書を読まずに推測で書き始める。

### ルール3：プロンプト指示ではなくスキルを使う

自然文でのプロンプト指示は禁止。各スキル（`/impl-api`, `/impl-screen`, `/write-tests`, `/write-e2e` 等）が設計書と `consumes` 依存関係を自動的に読み込んで実装を行うため、常にスキルコマンドのみを入力する。

---

# 準備フェーズ

## STEP 1  動作確認を行う

■ ターミナル
```bash
node scripts/check-docs.mjs
```

■ 確認
- [ ] `node scripts/check-docs.mjs` が最後まで通り、`エラー: 0 件, 警告: 0 件` が出る

## STEP 2  Git リポジトリを作って GitHub へ上げる

■ ターミナル
```bash
git init
git add -A
git commit -m "chore: 設計書および開発環境ハーネスの初期構築"
gh repo create realtimemd --private --source=. --push
```

`gh` が未導入なら GitHub 上で空リポジトリを作り、次を実行する。

```bash
git remote add origin https://github.com/<ユーザー名>/realtimemd.git
git branch -M main
git push -u origin main
```

■ 確認
- [ ] GitHub 上でファイルが見える
- [ ] `main` ブランチにプッシュされている

## STEP 3  main ブランチを保護する

■ ターミナル
```bash
gh api -X PUT repos/:owner/realtimemd/branches/main/protection \
  -f "required_status_checks[strict]=true" \
  -F "required_status_checks[contexts][]=設計書の整合性 (L6)" \
  -F "enforce_admins=false" \
  -F "required_pull_request_reviews=null" \
  -F "restrictions=null"
```

■ 確認
- [ ] GitHub の Settings → Branches に main の保護ルールが表示される

> 一人開発でも設定する。Agentが指示によって main へ直接コミットしてしまう事故を防ぐ。

## STEP 4  Agent を起動して設定を確認する

■ ターミナル
```bash
claude
```

■ Agent
```
/context
```

■ 確認
- [ ] Memory files またはコンテキスト情報に `AGENTS.md` が読み込まれている

## STEP 5  スラッシュコマンド（スキル）が認識されているか確認する

■ Agent
```
/
```

■ 確認
- [ ] 一覧に `impl-api` `impl-screen` `write-tests` `write-e2e` `review-docs` `ship` `fix` `extend-api` `merge-parallel` が出る

■ Agent
```
/clear
```

---

# M1：ドキュメント作成・更新・リアルタイムプレビュー（直列）

**ゴール**：ドキュメントを新規作成・保存でき、Markdownがリアルタイムにプレビュー表示される。

## STEP 6  ブランチを切る

■ ターミナル（Agent はいったん終了する）
```bash
git switch -c m1-create-and-preview
claude
```

■ 確認
- [ ] `git branch` で `m1-create-and-preview` に `*` が付いている

## STEP 7  メイン画面のE2Eテストを先に書く

> **この STEP を飛ばさない。** ガードレールを先に置くのが目的。
> 画面が未実装なのでテストは落ちる。それが正しい。

■ Agent
```
/write-e2e SCR-0101
```

■ 終わったら
```
/ship "SCR-0101 のE2Eテスト（実装前・落ちる状態）"
```

■ 確認
- [ ] `tests/e2e/` にファイルが生成されている
- [ ] タイトル入力・本文編集・プレビューレンダリングのシナリオが含まれている
- [ ] テストは落ちている（画面がまだ無いので正常）

■ Agent
```
/clear
```

## STEP 8  ドキュメント作成APIを実装する

■ Agent
```
/impl-api API-0102
```

■ 終わったら
```
/ship "API-0102 ドキュメント作成API"
```

■ 確認
- [ ] 完了報告に `node scripts/check-docs.mjs: PASS` が確認できる
- [ ] 要確認事項が「なし」である（あれば内容を読んで判断する）
- [ ] `app/schemas/` および `app/api/v1/` に設計書通りのコードが追加されている

■ うまくいかないとき

| 症状 | 打つもの |
|---|---|
| チェックが落ちたまま報告された | `/fix <エラー内容>` |
| 設計書にないエラーコードが作られた | `/review-docs API-0102` で指摘票を作らせる |

■ Agent
```
/clear
```

## STEP 9  ドキュメント作成APIのテストを書く

■ Agent
```
/write-tests API-0102
```

■ 終わったら
```
/ship "API-0102 の単体テスト"
```

■ 確認
- [ ] **観点消化表**が報告に出ている
- [ ] 必須(○)の観点がすべて「消化」になっている
- [ ] サイズ超過エラー (2MB) やタイトル必須チェックが検証されている

■ うまくいかないとき

必須観点が消化されていない場合、そのまま次へ進まない。次を打つ。

```
/write-tests API-0102
```

■ Agent
```
/clear
```

## STEP 10  ドキュメント更新APIを実装する

■ Agent
```
/impl-api API-0103
```

■ 終わったら
```
/ship "API-0103 ドキュメント更新API"
```

■ 確認
- [ ] `updated_at` の更新が設計書通りに行われている
- [ ] ドキュメント未存在時 (404) のエラーハンドリングが実装されている

■ Agent
```
/clear
```

## STEP 11  ドキュメント更新APIのテストを書く

■ Agent
```
/write-tests API-0103
```

■ 終わったら
```
/ship "API-0103 の単体テスト"
```

■ 確認
- [ ] 正常系更新および 404 / 400 エラー系の観点が消化されている

■ Agent
```
/clear
```

## STEP 12  プレビューレンダリングAPIを実装する

■ Agent
```
/impl-api API-0201
```

■ 終わったら
```
/ship "API-0201 プレビューHTMLレンダリングAPI"
```

■ 確認
- [ ] Markdownから安全なHTMLへの変換処理が実装されている

■ Agent
```
/clear
```

## STEP 13  プレビューレンダリングAPIのテストを書く

■ Agent
```
/write-tests API-0201
```

■ 終わったら
```
/ship "API-0201 の単体テスト"
```

■ Agent
```
/clear
```

## STEP 14  メインエディタ＆リアルタイムプレビュー画面を実装する

■ Agent
```
/impl-screen SCR-0101
```

■ 終わったら
```
/ship "SCR-0101 メインエディタ＆リアルタイムプレビュー画面"
```

■ 確認
- [ ] 4状態（読込中/0件/正常/エラー）の実装内容が含まれている
- [ ] `data-testid` が設計書の文字列と一致している (`doc-title-input`, `doc-editor-textarea`, `doc-preview-pane` など)

■ Agent
```
/clear
```

## STEP 15  E2Eテストを通す

■ ターミナル
```bash
npm run test:e2e
```

■ 落ちたら Agent
```
/fix E2Eテスト tests/e2e/scr-0101-main-editor.spec.ts が落ちています
```

`/fix` は原因分類を報告する。

| 報告された分類 | 次に打つもの |
|---|---|
| A. 実装のバグ | `/fix 原因Aの修正を適用してください` |
| B. テストのバグ | `/fix 原因Bの修正を適用してください` |
| C. 設計書の欠陥 | **止まる。** STEP 17 へ |
| D. 観点の不足 | 観点表の追加。STEP 17 へ |

■ 終わったら
```
/ship "SCR-0101 のE2Eテストを通した"
```

■ Agent
```
/clear
```

## STEP 16  設計書のセルフレビュー

■ Agent
```
/review-docs API-0102 API-0103 API-0201 SCR-0101
```

■ 終わったら
```
/ship "M1 対象設計書のレビュー指摘票"
```

■ 確認
- [ ] 指摘があれば `docs/reviews/` に指摘票が作成されている

■ Agent
```
/clear
```

## STEP 17  設計変更が必要になった場合のみ実行する

> 不要ならこの STEP は飛ばす。

設計書の変更は**実装セッションとは別に行う**。フックで `docs/` の編集はブロックされている。

■ ターミナル
```bash
# Agent を終了してから
git switch main
git switch -c docs/m1-fixes
ALLOW_DOCS_EDIT=1 claude
```

■ Agent
```
/review-docs API-0102 API-0103 API-0201 SCR-0101
```

■ 終わったら
```
/ship "設計書の修正"
```

■ その後
```bash
gh pr merge --squash --delete-branch
git switch m1-create-and-preview
git merge main
```

## STEP 18  M1 のPRを作ってマージする

■ Agent
```
/ship "M1: ドキュメント作成・更新・リアルタイムプレビュー機能の完了"
```

■ PRの完了確認（★ここが人間の仕事）
- [ ] `node scripts/check-docs.mjs` が通る
- [ ] `SCR-0101` のE2Eテストが通る
- [ ] **PRの差分を全部読む**。設計書と乖離した実装になっていないか確認する

■ ターミナル
```bash
gh pr merge --squash --delete-branch
git switch main
git pull
```

**M1 完了。**

---

# M2：一覧取得・削除・エクスポート（並列化デビュー）

**ゴール**：ドキュメント一覧が表示・選択・削除でき、PDF/HTMLエクスポートモーダルからダウンロードできる。

> M1 を直列でやったことで、スキルの動作とガードレールの仕組みが分かったはず。
> ここから並列化を活用する。

## STEP 19  ブランチを切る

■ ターミナル
```bash
git switch -c m2-list-delete-export
claude
```

## STEP 20  2つのAPIを並列で実装する

■ Agent
```
API-0101（一覧取得）と API-0104（ドキュメント削除）を、
それぞれ別の api-implementer サブエージェントで並列に実装してください。
各サブエージェントは /impl-api を使用し、共通ファイルは変更しないでください。
```

■ 確認
- [ ] 2つのサブエージェントの報告が返ってきた
- [ ] 共有ファイルが勝手に上書きされていない

## STEP 21  並列の成果を集約する

> **この STEP を飛ばすとルーティングや型登録が漏れる。**

■ Agent
```
/merge-parallel API-0101 API-0104
```

■ 終わったら
```
/ship "API-0101/0104 の実装（並列実装＋集約）"
```

■ 確認
- [ ] `node scripts/check-docs.mjs` が PASS
- [ ] `app/main.py` に2つのルートが登録されている

■ Agent
```
/clear
```

## STEP 22  2つのAPIのテストを並列で書く

■ Agent
```
API-0101 と API-0104 の単体テストを、
それぞれ別の test-writer サブエージェントで /write-tests を使用して並列に書いてください。
```

■ 終わったら
```
/ship "API-0101/0104 の単体テスト"
```

■ 確認
- [ ] 2つとも観点消化表が出ている
- [ ] ページネーション（limit/offset）や削除後の404確認が検証されている

■ Agent
```
/clear
```

## STEP 23  PDF/HTMLエクスポートAPIを実装する

■ Agent
```
/impl-api API-0301
```

■ 終わったら
```
/ship "API-0301 PDF/HTMLエクスポートAPI"
```

■ 確認
- [ ] PDF生成（A4/Letter対応）およびHTMLエクスポート処理が実装されている

■ Agent
```
/clear
```

## STEP 24  エクスポートAPIのテストを書く

■ Agent
```
/write-tests API-0301
```

■ 終わったら
```
/ship "API-0301 の単体テスト"
```

■ Agent
```
/clear
```

## STEP 25  エクスポート設定モーダル画面を実装する

■ Agent
```
/impl-screen SCR-0301
```

■ 終わったら
```
/ship "SCR-0301 エクスポート設定モーダル"
```

■ 確認
- [ ] `export-format-radio`, `export-paper-select`, `btn-submit-export` が実装されている

■ Agent
```
/clear
```

## STEP 26  メイン画面に一覧・削除・エクスポート導線を追加する

> 既存画面の差分拡張なので `/extend-api` を使う。

■ Agent
```
/extend-api SCR-0101 一覧取得・削除・エクスポートモーダル連携の追加
```

■ 終わったら
```
/ship "SCR-0101 に一覧・削除・エクスポート導線を追加"
```

■ 確認
- [ ] 「未実装箇所」の差分表が報告に出ている
- [ ] 既存の機能（編集・プレビュー）が壊れていない

■ Agent
```
/clear
```

## STEP 27  エクスポートモーダルのE2Eテストを作成・通過させる

■ Agent
```
/write-e2e SCR-0301
```

■ ターミナル
```bash
npm run test:e2e
```

■ 落ちたら Agent
```
/fix E2Eテストが落ちています
```

■ 終わったら
```
/ship "SCR-0301 のE2Eテストを通した"
```

■ Agent
```
/clear
```

## STEP 28  乖離チェック

■ Agent
```
/review-docs API-0101 API-0104 API-0301 SCR-0301
```

■ 終わったら
```
/ship "M2 対象設計書のレビュー指摘票"
```

■ Agent
```
/clear
```

## STEP 29  M2 のPRを作ってマージする

■ Agent
```
/ship "M2: 一覧取得・削除・エクスポート機能の完了"
```

■ ターミナル
```bash
gh pr merge --squash --delete-branch
git switch main
git pull
```

**M2 完了。ここでMarkdownアプリの主要機能が全て動作する。**

---

# M3：CI整備・全体品質検証・出荷

**ゴール**：CIパイプラインが構築され、全テスト・整合性チェックが完全自動化されて正式リリースできる。

## STEP 30  ブランチを切る

■ ターミナル
```bash
git switch -c m3-ci-quality
claude
```

## STEP 31  GitHub Actions CI パイプラインを構築・検証する

■ Agent
```
/review-docs API-0101 API-0102 API-0103 API-0104 API-0201 API-0301 SCR-0101 SCR-0301
```

■ 終わったら
```
/ship "GitHub Actions CI パイプライン整備と全設計書整合性検証"
```

■ Agent
```
/clear
```

## STEP 32  全テスト・センサーの一括実行

■ ターミナル
```bash
node scripts/check-docs.mjs
pytest tests/
npm run test:e2e
```

■ 確認
- [ ] `node scripts/check-docs.mjs` が エラー: 0 件, 警告: 0 件
- [ ] 全ての単体テスト・E2Eテストが PASS

## STEP 33  M3 のPRを作って正式出荷（Release）する

■ Agent
```
/ship "M3: Realtime Markdown App 正式リリース"
```

■ ターミナル
```bash
gh pr merge --squash --delete-branch
git switch main
git pull
```

**完成・出荷完了。**

---

# 困ったときの早見表

| 症状 | 打つもの |
|---|---|
| テストが落ちた | `/fix <落ちているテスト名>` |
| `check-docs` が落ちる | `/fix node scripts/check-docs.mjs が落ちています` |
| 設計書の整合性エラーでターンが終わらない | `check-docs` の出力を読んで `/review-docs` を実行する |
| 設計書が曖昧で実装できない | 実装を止めて STEP 17 の手順で設計を直す |
| `docs/` を編集しようとしてブロックされた | 正常な動作。設計変更は STEP 17 の手順で |
| 並列実行がうまくいかない | 直列（`/impl-api` を1つずつ）に戻す |
| Agent が設計書を読まずに書き始めた | `/clear` してやり直す |

# やってはいけないこと

| 禁止 | 理由 |
|---|---|
| 自然文プロンプトで実装を指示する | 設計書と規約を無視した自己流コードが生成されるため、必ずスキルを使う |
| `/ship` を打たずに次の STEP へ進む | 手元にしか履歴がない状態が生まれる |
| `/clear` せずに複数 STEP を続ける | 前の作業の前提を引きずり、設計書を読まなくなる |
| E2Eテストの STEP を後回しにする | ガードレールなしで生成が進み、後工程にバグが流出する |
| 必須観点の未消化を見逃す | この段階でしか検出できない |
| テストを通すために実装の検証を緩める | 品質の根拠が失われる |
| main に直接コミットする | ブランチ保護設定により失敗する。必ず PR 経由でマージする |
| M1 から並列化する | 挙動を理解しないうちの量産はレビューが破綻する |

## 要確認事項
なし
