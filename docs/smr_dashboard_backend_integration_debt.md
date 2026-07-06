# Dashboard 后台集成技术债文档

## 1. 当前 Dashboard 页面状态总览

| 页面 | 阶段 | 前台形态 | 后台接入 | data_status |
|---|---|---|---|---|
| 今日总览 | SMR-D1 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| 覆盖池 | SMR-D4 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| 信号流 | SMR-D2 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| 研究队列 | SMR-D3 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| 数据健康 | SMR-D5 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |

## 2. 今日总览（SMR-D1）

### 当前状态

- **前台形态**：已完成，包含 4 张 KPI 卡片、今日最重要的 3 件事、今日待判断、覆盖池异动、数据健康提醒
- **后台接入**：未接入，数据来自现有 dashboard state 的轻量映射

### 轻量映射模块

| UI 模块 | 当前数据来源 |
|---|---|
| KPI 卡片 | overview、current_state |
| 今日最重要的 3 件事 | daily_report、opportunity |
| 今日待判断 | review_queue、risk_decision |
| 覆盖池异动 | coverage_moves、current_state |
| 数据健康提醒 | health_summary |

### 需要真实后台数据

| 模块 | 需要的后台数据 | 优先级 |
|---|---|---|
| KPI 卡片 | 实时计算的今日数据 | 高 |
| 今日最重要的 3 件事 | 真实的今日事件/信号 | 高 |
| 今日待判断 | 真实的待审核事项 | 高 |
| 覆盖池异动 | 真实的价格/成交量异动 | 高 |
| 数据健康提醒 | 真实的数据质量指标 | 中 |

## 3. 信号流（SMR-D2）

### 当前状态

- **前台形态**：已完成，包含信号时间线、今日信号摘要、热门关联对象、信号来源分布
- **后台接入**：未接入，数据来自现有 dashboard state 的轻量映射

### 轻量映射模块

| UI 模块 | 当前数据来源 |
|---|---|
| 信号时间线 | evidence_gaps、daily_report |
| 今日信号摘要 | overview、current_state |
| 热门关联对象 | strategy_watch、opportunity |
| 信号来源分布 | 静态占位 |

### 需要真实后台数据

| 模块 | 需要的后台数据 | 优先级 |
|---|---|---|
| 信号时间线 | 真实的信号/证据流 | 高 |
| 今日信号摘要 | 真实的信号聚合统计 | 高 |
| 热门关联对象 | 真实的对象热度排序 | 中 |
| 信号来源分布 | 真实的来源分布统计 | 中 |

## 4. 研究队列（SMR-D3）

### 当前状态

- **前台形态**：已完成，包含研究队列列表、研究详情、证据缺口、人工动作按钮
- **后台接入**：未接入，数据来自现有 dashboard state 的轻量映射

### 轻量映射模块

| UI 模块 | 当前数据来源 |
|---|---|
| 研究队列列表 | evidence_gaps、strategy_watch、risk_decision、opportunity、daily_report |
| 研究详情 | 选中队列项的轻量映射 |
| 证据缺口 | evidence_gaps 或默认占位 |
| KPI 卡片 | 队列项统计 |

### 需要真实后台数据

| 模块 | 需要的后台数据 | 优先级 |
|---|---|---|
| 研究队列列表 | 真实的研究任务队列 | 高 |
| 研究详情 | 真实的研究假设和证据 | 高 |
| 证据缺口 | 真实的证据缺口分析 | 高 |
| 人工动作按钮 | 真实的审核接口 | 高 |
| KPI 卡片 | 实时计算的研究队列统计 | 中 |

## 5. 覆盖池（SMR-D4）

### 当前状态

- **前台形态**：已完成，包含覆盖对象列表、覆盖详情、证据概览、缺失证据、覆盖分布、优先级热区
- **后台接入**：未接入，数据来自现有 dashboard state 的轻量映射

### 轻量映射模块

| UI 模块 | 当前数据来源 |
|---|---|
| 覆盖对象列表 | strategy_watch、opportunity_radar、daily_report、evidence_gaps、risk_monitor |
| 覆盖详情 | 选中队列项的轻量映射 |
| 证据概览 | evidence_count / gap_count 轻量计算 |
| 缺失证据 | evidence_gaps 或默认占位 |
| 覆盖分布 | 覆盖对象类型统计 |
| 优先级热区 | 筛选 priority=高 的对象 |

### 需要真实后台数据

| 模块 | 需要的后台数据 | 优先级 |
|---|---|---|
| 覆盖对象列表 | 真实的 coverage object store | 高 |
| 覆盖详情 | 真实的公司/行业/主题详情 | 高 |
| 证据概览 | 真实的 evidence completeness 计算 | 高 |
| 缺失证据 | 真实的证据缺口分析 | 高 |
| 覆盖分布 | 真实的覆盖实体映射 | 中 |
| 优先级热区 | 真实的优先级排序 | 中 |

## 6. 数据健康（SMR-D5）

### 当前状态

- **前台形态**：已完成，包含 4 张 KPI 卡片、关键健康问题列表、系统模块健康度、数据源状态分布、今日运行摘要
- **后台接入**：未接入，数据来自现有 dashboard state 的轻量映射
- **Foundation 输入流**：待接入，data_status = pending_backend_integration

### 轻量映射模块

| UI 模块 | 当前数据来源 |
|---|---|
| 行情新鲜度 | overview.lag_days / market_lag_days |
| 信息源可用率 | source_registry.sources 健康比例 |
| 关键阻塞问题 | risk_monitor.alerts P0/P1 计数 |
| 证据流水线状态 | pipeline.overall_status |
| 关键健康问题列表 | risk_monitor.issues / alerts |
| 系统模块健康度 | source_registry + 默认配置 |
| 数据源状态分布 | 模块健康度聚合 |
| 今日运行摘要 | pipeline summary / overview |

### 需要真实后台数据

| 模块 | 需要的后台数据 | 优先级 |
|---|---|---|
| 行情新鲜度 | 实时市场行情 freshness 检查 | 高 |
| 信息源可用率 | 真实的 source health 生命周期管理 | 高 |
| 关键阻塞问题 | 真实的 blocking issue 生命周期 | 高 |
| 证据流水线状态 | 真实的 evidence pipeline health 监控 | 高 |
| 关键健康问题列表 | 真实的 health issue store | 高 |
| 系统模块健康度 | 真实的 module health monitor | 中 |
| 数据源状态分布 | 真实的 source health aggregation | 中 |
| 今日运行摘要 | 真实的 daily run summary | 中 |
| Foundation 输入流 | Foundation SourceHealth inflow | 高（SMR-D7） |

## 7. 真实后台挂钩缺口

### 缺口总览

1. **审核接口**：缺少安全的审核接口，无法实现通过/补证据/暂缓/驳回的真实状态变更
2. **研究任务管理**：缺少研究任务的创建、更新、追踪后端服务
3. **证据管理**：缺少证据的收集、存储、关联后端服务
4. **覆盖池管理**：缺少真实的 coverage object store 和覆盖状态生命周期管理
5. **Foundation 数据流**：缺少 opc-foundation 证据流入 Dashboard 的通道
6. **实时数据更新**：缺少实时数据推送机制，当前为静态快照
7. **用户权限**：缺少用户权限管理，无法区分不同角色的操作权限

### 缺口优先级

| 缺口 | 优先级 | 预计工作量 |
|---|---|---|
| 审核接口 | 高 | 3-5 天 |
| Foundation 数据流 | 高 | 5-7 天 |
| 研究任务管理 | 高 | 5-7 天 |
| 证据管理 | 中 | 3-5 天 |
| 实时数据更新 | 中 | 3-5 天 |
| 用户权限 | 低 | 2-3 天 |

## 8. Foundation 数据流入缺口

### 当前状态

- Foundation 仅作为"Foundation 待接入"出现在证据缺口的目标来源中
- 未真实接入 opc-foundation
- 未创建 Foundation 数据流

### 需要的 Foundation 输入

| Foundation 输出 | Dashboard 输入 | 用途 |
|---|---|---|
| 证据包 | 研究详情的已有证据 | 补充研究假设的证据支持 |
| 证据缺口分析 | 证据缺口列表 | 识别缺失的证据 |
| 研究任务建议 | 研究队列 | 生成值得深挖的研究主题 |
| 信号强度评估 | 信号时间线 | 评估信号的可信度 |
| 风险预警 | 数据健康 | 监控数据质量风险 |

### 数据流设计

```text
Foundation Runner
    ↓
Foundation Evidence Output (JSON)
    ↓
Foundation Bridge (SMR-D7)
    ↓
Dashboard State / SQLite
    ↓
Dashboard View Models
    ↓
Dashboard Pages
```

## 9. 后续建议阶段

### SMR-D5：数据健康页面 ✅ 已完成

- 实现数据健康页面
- 展示数据质量指标
- 监控各数据源状态
- 告警和异常提示

### SMR-D6：Dashboard 后台真实挂钩

- 接入真实审核接口
- 实现研究任务管理后端
- 实现证据管理后端
- 接入用户权限系统
- 实现数据健康真实监控闭环

### SMR-D7：Foundation Evidence Inflow

- 创建 Foundation Bridge
- 实现 Foundation 证据流入 Dashboard
- 建立证据包与研究队列的关联
- 实现信号强度评估展示
- 接入 Foundation SourceHealth inflow

## 10. 技术债管理策略

### 短期（当前阶段）

- 保持轻量映射，确保前台形态完整
- 标记所有数据来源状态
- 记录技术债，不急于解决

### 中期（SMR-D6）

- 优先解决高优先级缺口
- 实现核心审核流程
- 建立基础的后台服务

### 长期（SMR-D7+）

- 完成 Foundation 接入
- 实现完整的研究闭环
- 建立实时数据更新机制

## 11. 注意事项

1. **不得夸大**：当前页面不得展示"已完成真实接入""已形成自动研究闭环"等误导性说法
2. **data_status**：所有 view model 输出必须包含 data_status 字段，明确数据来源状态
3. **空态设计**：数据缺失时必须展示清晰的空态，不得显示假数据
4. **安全边界**：接入后台时必须确保审核接口的安全性，防止未授权操作
5. **禁用词**：页面不得输出 target price、目标价、买入、卖出、建仓、仓位建议、组合建议等禁用词
