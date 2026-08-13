# TypeScript コーディング規約 (coding-typescript.md)

## 1. 型安全性の徹底
- `tsconfig.json` の `strict: true`, `noUncheckedIndexedAccess: true` を前提とする。
- `any` の使用は原則禁止（必要時は `unknown` と型ガードを使用）。
- `as` による強制的型キャストは禁止。

## 2. コンポーネントおよびロジック分離
- UIコンポーネント内に肥大化したビジネスロジックを書かず、Custom Hooks へ切り出す。
- インタラクティブ要素には必ず `data-testid` を設計書の指定通り付与する。
