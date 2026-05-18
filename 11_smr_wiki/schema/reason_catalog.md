# SMR Wiki Reason Catalog

当前阶段先收口最小原因码目录。

## Review Reason Codes

- `needs_human_judgement`
  - 用于高判断密度对象默认进入人工审核
- `duplicate_source`
  - 来源重复
- `duplicate_thesis`
  - 同一实体同一 thesis 已存在近似知识页
- `insufficient_evidence`
  - 证据不足
- `conflicts_with_latest_research`
  - 与最新研究结论冲突
- `outdated_conclusion`
  - 结论已过期
- `format_incomplete`
  - 结构不完整
- `source_not_reliable`
  - 来源可信度不足

## 使用原则

1. 原因码优先用于结构化治理，不用写成自由文本替代品。
2. 自由文本说明是补充，不是替代原因码。
3. 同一类治理动作尽量复用已有 code，不要不断发明新字符串。
