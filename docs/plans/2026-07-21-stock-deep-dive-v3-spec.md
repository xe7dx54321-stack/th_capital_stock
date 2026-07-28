# 个股深度研究 V3 — 产品与技术规格

## 1. 目标

把现有“事实清单 + 系统状态”升级为真正可阅读、可审计、可复现的个股深度研究工作流。V3 必须先制定研究计划，再按问题取证，形成结构化分析，使用模型撰写长文，并在事实、引用、完整性和表达四个维度通过质量门。

V3 仍是本地自用 MVP：只做研究，不自动交易，不自动批准投资记忆，不把模型输出写回基础事实表。

## 2. 用户可见成果

每次运行生成三个彼此分离的成果：

1. `stock_deep_dive_report`：只包含研究正文，不展示任务编号、隔离字段和运行日志。
2. `stock_research_packet_v2`：兼容现有接口的受治理研究包，新增 `research_v3` 扩展。
3. `stock_deep_dive_audit`：研究计划、数据源状态、覆盖矩阵、质量得分和降级原因。

正文标准结构：

1. 投资摘要与核心判断
2. 公司画像与商业模式
3. 行业阶段与需求驱动
4. 产品矩阵与核心竞争力
5. 经营模式、客户与供应链
6. 财务深度分析
7. 同行比较与竞争格局
8. 增长驱动与盈利预测边界
9. 估值分析
10. 催化剂与时间表
11. 风险、反面证据与证伪条件
12. 乐观/基准/谨慎情景
13. 后续跟踪指标
14. 结论
15. 证据索引

## 3. 核心流程

```text
validate_input
  -> provider_preflight
  -> resolve_research_identity
  -> build_research_plan
  -> collect_research_context
       -> official filings and document chunks
       -> approved/candidate memories
       -> company and industry news
       -> market events
       -> sector graph and peer universe
       -> target and peer instruments
  -> normalize_research_data
  -> build_research_packet
  -> build_deterministic_analysis
  -> compile_claims
  -> evidence_quality_gate
  -> write_governed_draft
  -> model_synthesis
  -> report_quality_gate
  -> repair_once_if_needed
  -> persist_report_packet_audit
```

## 4. 数据契约

V3 保留 `schema_version = 2.0`，避免破坏现有运行器和调用方；新增：

```json
{
  "workflow_version": "3.0",
  "research_v3": {
    "provider_status": {},
    "plan": {"sections": [], "questions": []},
    "corpus": {"filings": [], "chunks": [], "news": [], "events": [], "memories": []},
    "graph": {"sector": {}, "peers": []},
    "instruments": {"target": {}, "peers": []},
    "analysis": {"financial": {}, "business": {}, "valuation": {}, "risks": {}},
    "coverage": {"sections": [], "score": 0.0},
    "report_quality": {}
  }
}
```

所有语料项必须携带稳定 `evidence_id`、来源、日期、标题或章节、可使用范围。新闻只能用于背景、催化剂和风险，不得替代正式披露证明历史财务事实。

## 5. 分层降级

- 行情过期：仅阻断“当前估值/即时交易判断”，不得阻断历史经营分析。
- 同行财务缺失：同行章节降级为产品与价格表现比较，不影响公司自身分析。
- 新闻缺失：催化剂章节说明覆盖不足，不影响正式财报分析。
- 模型不可用或模型报告未过门：返回完整的确定性 V3 草稿，不回退到 V2 状态清单。
- 单个数据源失败：记录在 audit 中，其余分支继续。

## 6. 报告质量门

### 确定性检查

- 必须包含至少 12 个标准章节中的 10 个。
- 必须包含投资摘要、财务分析、风险与结论。
- 不得把执行信息、任务编号、隔离字段数量写进正文。
- 正文引用必须存在于 Research Packet。
- 数字事实必须来自正式证据或 `calculation` 记录。
- 模型报告目标为 8,000–15,000 个中文字符；确定性回退稿不得低于 4,000 字符。
- 章节覆盖率不低于 80%，引用覆盖率不低于 95%。

### 研究价值检查

- 至少给出 5 个有依据的经营判断。
- 至少解释 3 条“数据 -> 驱动因素 -> 投资含义”的因果链。
- 至少给出 5 个可跟踪指标。
- 至少给出 3 个风险及其预警信号/证伪条件。
- 估值输入失效时必须明确停在估值边界，不能伪造目标价。

## 7. 性能、可靠性与安全

- 本地深研允许 8 分钟总预算；模型单次调用最长 240 秒。
- 模型生成最多两次：首次成稿 + 一次修订，防止无限循环。
- 同一次 run 的数据库读取保持只读；只有 control DB 和 artifact 目录允许写入。
- API 密钥只从环境变量读取，不写入 Packet、日志或 artifact。
- 运行必须幂等地保存阶段事件；模型失败不丢失受治理草稿。

## 8. 验收案例

主金标准为 `300308.SZ`。报告必须正确呈现并引用 2025 年报中的收入、归母净利润、扣非净利润、经营现金流、EPS、ROE、资产和净资产的三年比较；必须讨论高速光模块、800G/1.6T、硅光平台、以销定产、客户认证、产销量和毛利率变化；必须说明当前行情与估值数据时点，并把不可靠估值字段局部降级。

通过后再用至少 3 个不同行业标的回归，验证工作流不会把中际旭创专属内容硬编码到其他公司报告。
