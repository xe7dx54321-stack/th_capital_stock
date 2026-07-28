# 个股深度研究 V2 设计

## 目标与边界

本阶段只优化 `stock_deep_dive`。目标不是生成更长的报告，而是建立一条能够反复验证的研究流水线：原始数据先经过字段级标准化和一致性检查，再形成 Research Packet，随后由确定性分析器编译事实、变化、证据缺口、情景和研究边界。模型只能改写已经通过验证的结构化判断，不得直接读取杂乱原始数据后补造事实。

V2 继续保持只读、不交易、不产生目标价、不自动批准记忆。网络采集和聊天入口整合不进入第一批；先把本地受治理工作流做成唯一权威内核。

## 方案比较

考虑过三种方案：

1. 继续增强 JavaScript 聊天报告函数。改动快，但会与 Python 受治理工作流继续分叉。
2. 复活 Phase 35–85 的历史研究脚本。覆盖面大，但一次性阶段脚本过多，维护成本高。
3. 在 `smr_app` 内建立稳定的 Research Packet v2，并让所有入口逐步复用。初期需要梳理契约，但最适合一个工作流一个工作流打磨。

采用第三种方案。历史脚本只作为方法论参考，不重新进入生产调用链。

## 权威工作流

```text
validate_input
  → load_context
  → normalize_research_data
  → build_research_packet
  → compile_claims
  → quality_gate
  → write_outputs
```

`load_context` 只负责读取；`normalize_research_data` 对每个字段给出 `valid / quarantined / missing`；`build_research_packet` 生成稳定 JSON；`compile_claims` 只消费有效字段；`quality_gate` 决定报告是 `research_ready`、`evidence_limited` 还是 `cannot_conclude`。

## Research Packet v2

顶层字段固定为：

- `schema_version`、`ticker`、`market`、`generated_at`
- `identity`
- `datasets.fundamentals / valuation / evidence / risk / market`
- `quality.issues / blockers / usable_evidence_ids / quarantined_fields`
- `claims`、`scenarios`、`evidence_gaps`

每个可研究字段包含：数值、单位、报告期、来源证据、状态和隔离原因。报告不得直接读取原始快照。

## 数据校验规则

基本面核心字段必须有报告期和证据编号。百分比统一保存为小数；金额保留原币种。毛利润明显高于营收、净利润绝对值显著超过营收、EPS 超出基础范围、比率超出合理边界时，对相关字段隔离而不是自动猜单位。来源写着 `fresh` 不能覆盖结构性错误。

估值只在日期、允许用途和基础范围同时有效时进入研究上下文；没有独立证据编号时只能作为未引用背景，不能生成估值判断。公告证据需要保留来源、发布日期、质量分和核心观点可用性。

## 质量标准

- 被隔离字段进入最终报告的数量必须为 0。
- 所有可审计判断必须有实际存在的证据编号。
- 没有报告期的基本面快照不得标为可研究。
- 没有独立证据的估值不得形成高估、低估或目标价结论。
- 输入缺失时正常完成工作流并返回 `cannot_conclude`，不能伪造补全。
- Research Packet 必须作为 JSON artifact 持久化，报告能够从同一 Packet 重建。

## 测试策略

第一层测试字段单位、报告期、交叉一致性和隔离原因；第二层测试 Packet 的证据闭包与质量状态；第三层用 A/H/US fixtures 验证工作流和 artifact；最后用真实本地数据跑中际旭创等代表标的，人工核对脏字段不会泄漏到报告。
