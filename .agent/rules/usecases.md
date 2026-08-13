---
paths:
  - "src/usecases/**/*.ts"
  - "app/usecases/**/*.py"
  - "app/domain/**/*.py"
---

ユースケース層・ドメイン層を書くときは、対象のAPI設計書の
「3. 事前条件/事後条件/不変条件」と「6. 処理順序の指定」を満たすこと。

**現在時刻は引数 `now` で受け取る。** この層で `new Date()` や `datetime.now()` を
呼ぶと L1 センサー(ESLint/Linter)が落ちる（テストで時刻を固定できなくなるため）。
