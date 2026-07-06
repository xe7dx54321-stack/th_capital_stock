# SMR-D3 Dashboard 研究队列施工报告

## 1. 执行时间

- 执行日期：2026-07-06
- 执行时长：约 4 小时

## 2. Base Commit

- base branch: feature/smr-d2-dashboard-signal-flow
- base commit: 80dfbd4
- work branch: feature/smr-d3-dashboard-research-queue

## 3. 当前 Dashboard 启动方式

```bash
python3 08_scripts/dashboard/run_control_tower.py --host 127.0.0.1 --port 8877
```

## 4. 新增/修改文件

### 新增文件

| 文件 | 说明 |
|---|---|
| `08_scripts/dashboard/research_queue_view_model.py` | 研究队列 view model 数据适配层 |
| `tests/test_dashboard_research_queue.py` | 研究队列测试（15+ 测试用例） |
| `docs/smr_d3_dashboard_research_queue_report.md` | 施工报告 |
| `docs/smr_dashboard_backend_integration_debt.md` | 后台集成技术债文档 |

### 修改文件

| 文件 | 修改内容 |
|---|---|
| `08_scripts/dashboard/run_control_tower.py` | 新增 render_research_queue 渲染函数及相关辅助函数、CSS 样式 |
| `tests/test_dashboard_today_overview.py` | 更新 research placeholder 测试引用 |
| `tests/test_dashboard_signal_flow.py` | 更新 research placeholder 测试引用 |
| `docs/smr_d0_dashboard_product_blueprint.md` | 更新研究队列页面实现状态 |
| `docs/smr_d0_dashboard_data_mapping.md` | 更新研究队列数据映射 |

## 5. Page 4 研究队列实现范围

### 已实现模块

1. **页面标题区**：标题「研究队列」+ 副标题「待深挖主题管理 / 证据缺口 / 人工决策」
2. **顶部 KPI 卡片**：4 张卡片（待研究主题数、高优先级事项、待补证据事项、今日新增）
3. **左侧主区域**：研究队列列表，支持筛选和排序
4. **右上模块**：研究详情（主题标题、关联对象、优先级、研究假设、已有证据、缺失证据、下一步建议）
5. **右下模块**：证据缺口列表（缺口标题、重要性、目标来源、期望时间）
6. **底部免责声明**：「系统仅组织研究证据与待办，不直接给出投资建议。」
7. **人工动作按钮**：通过 / 补证据 / 暂缓 / 驳回（前台展示，不写真实状态）

### 未实现模块

- 真实后台状态写入逻辑（本阶段仅做前台展示）

## 6. KPI 实现情况

| KPI | 字段 | 状态 |
|---|---|---|
| 待研究主题数 | count + subtitle | 已实现 |
| 高优先级事项 | count + subtitle | 已实现 |
| 待补证据事项 | count + subtitle | 已实现 |
| 今日新增 | count + subtitle | 已实现 |

数据来源：从 dashboard state 的 evidence_gaps、strategy_watch、risk_decision、opportunity、daily_report 等字段轻量映射。

## 7. 研究队列列表实现情况

### 列表字段

- rank：排名
- title：标题
- related_entities：关联实体
- related_topics：关联主题
- priority：优先级（高/中/低）
- status：状态（研究中/初步研究/待验证/证据收集中/暂缓/已驳回/已通过）
- evidence_count：已有证据数
- gap_count：证据缺口数
- updated_at：更新时间
- short_reason：简要原因
- actions：操作按钮

### 状态枚举

```text
研究中 | 初步研究 | 待验证 | 证据收集中 | 暂缓 | 已驳回 | 已通过
```

### 优先级枚举

```text
高 | 中 | 低
```

### 动作按钮

```text
通过 | 补证据 | 暂缓 | 驳回
```

### 空态

```text
暂无研究队列
当前没有待深挖主题。请查看信号流或等待系统生成新的证据缺口。
```

## 8. 研究详情实现情况

### 详情字段

- title：主题标题
- related_entities：关联公司/行业/主题标签
- related_topics：关联主题
- priority：优先级 badge
- research_hypothesis：研究假设
- existing_evidence：已有证据列表
- missing_evidence：缺失证据列表
- next_steps：下一步建议
- risk_flags：风险标记

### 文案要求

- 只描述研究假设，不给投资结论
- 下一步建议只能是研究动作（补充公司 IR 数据、查找电话会原文、补充行业需求验证、等待更多证据）
- 不出现买入/卖出/目标价/仓位建议

### 空态

```text
请选择研究主题
当前没有可展示的研究详情。
```

## 9. 证据缺口实现情况

### 缺口字段

- gap_title：缺口标题
- importance：重要性（重要/中等/低）
- target_source：目标来源（公司 IR、行业调研、公开资料、电话会原文、第三方数据库等）
- expected_time：期望时间
- status：状态

### 重要性枚举

```text
重要 | 中等 | 低
```

### 目标来源示例

```text
公司 IR | 官方公告 | 行业调研 | 公开资料 | 电话会原文 | 第三方数据库 | Foundation 待接入
```

### 空态

```text
暂无证据缺口
```

## 10. 数据来源映射

| UI 模块 | 当前数据来源 | 数据状态 | 缺失时处理 |
|---|---|---|---|
| 待研究主题数 | evidence_gaps + strategy_watch + risk_decision + opportunity + daily_report | lightweight_mapping | 显示 0 |
| 高优先级事项 | 筛选 priority=高 的队列项 | lightweight_mapping | 显示 0 |
| 待补证据事项 | 各队列项 gap_count 之和 | lightweight_mapping | 显示 0 |
| 今日新增 | 更新时间为今日的队列项 | lightweight_mapping | 显示 0 |
| 研究队列列表 | evidence_gaps / strategy_watch.top_focus_items / risk.decision.sell_candidates / opportunity.markets / daily_report.highlights | lightweight_mapping | 空态提示 |
| 研究详情 | 选中队列项的轻量映射 | lightweight_mapping | 空态提示 |
| 证据缺口 | evidence_gaps 或默认占位 | lightweight_mapping | 默认占位缺口 |

## 11. 数据真实性说明

**重要声明**：

1. D1 今日总览、D2 信号流、D3 研究队列目前都是 Dashboard 前台形态建设
2. 当前数据多来自现有快照的轻量映射，不代表已经完成真实后台闭环
3. 页面不得展示"已完成真实接入""已形成自动研究闭环"等误导性说法
4. view model 输出包含 data_status 字段：
   - `real_snapshot`：真实快照数据
   - `lightweight_mapping`：轻量映射数据
   - `empty_state`：空态
   - `pending_backend_integration`：待后台接入

## 12. 空态设计

### 研究队列为空

```text
暂无研究队列
当前没有待深挖主题。请查看信号流或等待系统生成新的证据缺口。
```

### 研究详情为空

```text
请选择研究主题
当前没有可展示的研究详情。
```

### 证据缺口为空

```text
暂无证据缺口
```

## 13. 是否接入 opc-foundation

- **否**：本阶段不接入 opc-foundation
- Foundation 仅作为未来占位在目标来源中显示

## 14. 是否修改投资业务逻辑

- **否**：未修改任何投资业务逻辑
- 未修改估值模型、预期差模型、组合/仓位/风控/交易信号逻辑

## 15. 是否输出 target price / 买卖建议 / 组合建议

- **否**：页面不输出任何投资建议相关内容
- 禁用词检查：target price、目标价、买入、卖出、建仓、仓位建议、组合建议等均不在页面中出现

## 16. 测试结果

### 测试文件

- `tests/test_dashboard_today_overview.py`：19 测试用例，全部通过
- `tests/test_dashboard_signal_flow.py`：26 测试用例，全部通过
- `tests/test_dashboard_research_queue.py`：34 测试用例，全部通过

### 测试覆盖范围

1. build_research_queue_view_model(None) 不报错
2. build_research_queue_view_model({}) 不报错
3. metrics 4 张卡片字段存在
4. queue_items 默认最多 20 条
5. selected_detail 结构存在
6. evidence_gaps 结构存在
7. filters 支持 priority / status / sort / q
8. 异常 filter 值不会导致 500
9. /research 页面 HTML 包含研究队列、研究详情、证据缺口、免责声明
10. 主导航仍然只有 5 个业务页面
11. 其他已完成页面 / 和 /signals 仍能 HTTP 200
12. 禁用词不出现在 /research HTML 中
13. 数据缺失时展示空态
14. data_status 字段存在
15. 不真实联网
16. 不调用 opc-foundation
17. 不写入真实状态

### compileall

```bash
python3 -m compileall 08_scripts
# 无语法错误
```

## 17. 下一步建议

1. **SMR-D4**：实现覆盖池页面
2. **SMR-D5**：实现数据健康页面
3. **SMR-D6**：Dashboard 后台真实挂钩（接入真实审核接口、Foundation 数据流）
4. **SMR-D7**：Foundation Evidence Inflow（Foundation 证据流入 Dashboard）

## 18. 页面 URL

```text
http://127.0.0.1:8877/research
```
