# コード構造・対応マップ (code-map.md)

設計書IDとコード上のディレクトリ・ファイルの対応関係を定義する。

## 1. 設計書とコードの対応

| 設計書ID | 生成・対応するコードの置き場所 |
|---|---|
| `API-XXXX` (Python FastAPI) | `app/api/v1/api_xxxx.py`, `app/usecases/`, `app/schemas/`, `tests/test_api_xxxx.py` |
| `SCR-XXXX` (React) | `src/pages/scr-xxxx-*.tsx`, `src/components/`, `tests/e2e/scr-xxxx.spec.ts` |
| `TBL-XXXX` (SQLite) | `app/models/tbl_xxxx.py`, `db/migrations/` |
| `MSG-0001` (メッセージ辞書) | `src/locales/ja.json`, `app/core/messages.py` |

## 2. 依存の向き
```
[Routes (app/api)] -> [Use Cases (app/usecases)] -> [Repositories (app/repositories)] -> (DB)
                                                  -> [Domain (app/domain)]
[React Pages (src/pages)] -> [React Hooks (src/hooks)] -> [API Client (src/api)]
```
- `domain` や `usecases` から直接 `new Date()` や外部I/Oを呼ばず、引数や抽象化リポジトリ経由で注入すること。
