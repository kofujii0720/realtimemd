# 設計書マップ (doc-map.md)

本プロジェクトにおける文書体系および「何を作るときに何を読むか」の依存構造を定義する。

## 1. 文書体系と依存関係
```
[REQ-XXXX 要件定義] ───> [UC-XXXX ユースケース]
  │                           │
  ├───────> [TBL-XXXX テーブル] │
  │                           │
  ├───────> [SCR-XXXX 画面] <─┤
  │                           │
  └───────> [API-XXXX API]  <─┘
               │
               ▼
   [VP-XXXX テスト観点表]
```

## 2. 読出ルール
| 作成・変更する対象 | 必須読み込み文書 |
|---|---|
| 画面 (SCR) | `UC-XXXX`, `MSG-0001`, `API-XXXX` |
| API | `UC-XXXX`, `TBL-XXXX`, `REQ-0003` |
| テーブル (TBL) | `UC-XXXX`, `REQ-0003` |
| テスト観点 (VP) | 対応する `API-XXXX`, `SCR-XXXX`, `TBL-XXXX`, `UC-XXXX` |
