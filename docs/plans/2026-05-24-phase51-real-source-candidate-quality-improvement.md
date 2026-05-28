# Phase 51 Real Source Candidate Quality Improvement v1

## 目标
- candidate quality diagnostics
- quoted span validator
- source traceability scoring
- chunk quality classifier
- quality gate calibration
- tracking-support candidate upsert
- research-only revalidation
- quality improvement dashboard

## 当前重点
300308.SZ:
  Phase 50 生成 9 个 candidates
  Phase 51 目标是让部分 downgraded candidates 进入 passed_tracking_support
  tracking-support 不等于 confirmed
  tracking-support 不等于 pending/order/trade

## 安全边界
- confirmed_variables_added=0
- usable_for_promotion_true=0
-敏感变量不 confirmed
