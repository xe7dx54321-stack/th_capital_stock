# 研究工作流质量门

阶段 14 的验收规则只有一条：**没有被真实执行和断言的能力，不算通过。**

旧版 `use_mock=True` 会直接构造全绿结果，`--skip-check-full` 也会把 G11
判为通过。该行为已经删除。现在：

- 六轮回放执行 Router V2、六个生产工作流测试、引用校验、记忆治理和六类前端视图测试。
- 十一种故障各自执行对应的真实故障路径；不是把 `crashed` 写死为 `false`。
- `npm run check:full` 没有实际通过时，G11 和 `final_pass` 必须是 `false`。
- `--mock` 被显式拒绝，避免模拟结果再次混入验收报告。

## 一键最终验收

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe tools\evaluate_conversation_workflows.py final
```

只有退出码为 `0`、`failed_gates` 为空且 `final_pass` 为 `true` 才算通过。
该命令会真实执行 `npm run check:full`，耗时取决于完整回归套件。

## 分项诊断

```powershell
.\.venv\Scripts\python.exe tools\evaluate_conversation_workflows.py replay
.\.venv\Scripts\python.exe tools\evaluate_conversation_workflows.py faults
.\.venv\Scripts\python.exe -m pytest tests\e2e\test_knevo_six_turn_replay.py -v
```

`final --skip-check-full` 只用于快速诊断。它会有意返回失败，因为硬门槛
G11 没有被执行，不能用于验收。

## 六轮业务回放

| 轮次 | 自然语言任务 | 目标任务图 |
|---|---|---|
| T1 | 阳光电源换仓海光信息 | `pair_switch_decision` |
| T2 | 海光信息经营驱动估值 | `operating_driver_valuation` |
| T3 | 超节点主题预期差筛选 | `theme_expectation_gap` |
| T4 | 星网锐捷市值纠错并重算 | `claim_correction` |
| T5 | DCI 催化缺失的产业因果解释 | `industry_causal_explainer` |
| T6 | 德科立九十天公司信号计划 | `company_signal_plan` |

每轮必须同时满足：

1. 自然语言被 Router V2 路由到注册表中的正确任务图；
2. 对应 Python 生产工作流测试实际通过；
3. 需要的业务制品被工作流测试验证；
4. 任何测试失败都会记录原命令、退出码和输出尾部。

## 十一种故障

LLM 不可用、Firecrawl 不可用、主数据源失败、缓存过期、来源冲突、
交易日边界、报告期/币种/单位错误、估值输入缺失、未知引用、纠错与
权威数据仍冲突、会话中断恢复，均有独立的实际组件测试。配置文件中的
`verification_id` 必须能映射到验收器中的一个真实命令，否则验收器报错。

## 人工验收仍不可省略

自动门槛通过只证明契约和回归基线。发布前还应在本地浏览器完成：

1. 用普通中文输入六类任务，不输入工作流 ID；
2. 正文首先展示业务结论，不展示运行编号、工具名和系统状态；
3. 五类制品视图可阅读，候选记忆可批准、拒绝和归档；
4. 刷新页面后任务、制品和会话状态可恢复；
5. 至少完成一次真实数据补证和一次真实模型调用，并保存可审计记录。
