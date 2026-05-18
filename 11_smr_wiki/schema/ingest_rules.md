# SMR Wiki Ingest Rules

## 1. 当前允许进入 source manifest 的对象

- 行业研究卡
- 个股研究卡
- 推荐卡
- 日报
- 调度板快照
- 风险快照
- 动态池快照
- 外部网页原始快照

## 2. 当前允许自动转 draft 的对象

- 上述所有 manifest source

但默认分两类：

- `ready`
  - 日报
  - 调度板
  - 动态池快照
- `review_required`
  - 行业研究
  - 个股研究
  - 推荐卡
  - 风险相关对象
  - 外部原始来源

## 3. Draft 最小字段

- `draft_id`
- `source_id`
- `draft_type`
- `entity_type`
- `entity_id`
- `title`
- `summary`
- `candidate_category`
- `candidate_tags`
- `governance_status`
- `approval_status`

## 4. 当前阶段禁止事项

- 不允许脚本直接把高判断内容写入正式 Wiki。
- 不允许绕过 source manifest 直接凭文件路径落正式知识页。
- 不允许把日报全文直接复制成正式知识页。
- 不允许把 raw external（原始外部来源）直接视为正式知识结论。
