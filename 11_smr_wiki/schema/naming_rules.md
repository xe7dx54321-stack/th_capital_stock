# SMR Wiki Naming Rules

## 1. 基本原则

- 目录按知识类型分，不按脚本来源分。
- 文件名优先用英文小写和下划线。
- 页面标题可以用中文，但文件名尽量稳定。
- 同一实体长期页要保持固定文件名，不要每次重建新页。

## 2. 目录规则

- `wiki/sectors/`
  - 行业主线长期页
- `wiki/stocks/`
  - 个股长期定位页
- `wiki/theses/`
  - 主题逻辑页
- `wiki/strategies/`
  - 策略页
- `wiki/playbooks/`
  - 执行手册页
- `wiki/risk_cases/`
  - 风险案例页
- `wiki/decisions/`
  - 决策记录页
- `wiki/timelines/`
  - 时间线与阶段快照页

## 3. 文件命名建议

- 行业页：`{sector_key}.md`
- 个股页：`{ts_code_lower}.md`
- 主题页：`{theme_key}.md`
- 策略页：`{strategy_key}.md`
- 风险案例页：`{date}_{entity}_{topic}.md`
- 决策页：`{date}_{entity}_{decision_topic}.md`
- 时间线页：`{entity}_{period}.md`

## 4. Frontmatter 最小字段

每个正式知识页至少包含：

- `page_id`
- `page_type`
- `entity_type`
- `entity_id`
- `title`
- `status`
- `sources`
- `updated_at`
