# SMR Wiki Governance Rules

## 1. 当前阶段的治理状态

- `ready`
- `review_required`
- `blocked`

## 2. 当前阶段的审批状态

- `auto_ready`
- `pending_manual_review`
- `approved`
- `rejected`
- `reopened`

## 3. 当前阶段的最小治理原则

1. 行业研究、个股研究、推荐卡、风险对象默认人工审核。
2. 时间线类对象可以先走 `ready`。
3. 只有通过治理的 draft 才能进入 `wiki/`。
4. 所有审核动作后续都要带原因码和时间戳。

## 4. 当前阶段的导入边界

- 本轮先做到 `source manifest -> ingest draft -> markdown export`
- review queue / resolution / import 是下一步施工项
