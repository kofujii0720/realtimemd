---
name: ship
description: 検証・コミット・プッシュ・PR作成を行うスラッシュコマンド
---

# /ship <成果物名>

`.agent/prompts/build/PRM-BLD-SHP-001.md` の手順に従い、検証を実行してコミット・PR作成を行います。

## 制約
- `node scripts/check-docs.mjs` および全テストが PASS していない場合は即座に中止します
