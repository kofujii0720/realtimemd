# Python (FastAPI) コーディング規約 (coding-python.md)

## 1. 型ヒントと Pydantic
- 全ての関数・メソッドに厳格な型ヒントを記述する。
- APIの入出力スキーマには Pydantic BaseModel を使用し、バリデーションルールを明確に定義する。

## 2. アーキテクチャと依存性
- `app/api/` (ルーター) -> `app/usecases/` (業務ロジック) -> `app/repositories/` (DBアクセス) のレイヤー分離を維持する。
- リポジトリ層以外からSQL文や直接のDB接続を行わない。
- 時刻取得は `usecases` 内で直接 `datetime.now()` を行わず、引数で外部注入するか専用サービス経由とする。
