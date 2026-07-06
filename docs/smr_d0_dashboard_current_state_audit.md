# SMR-D0 Dashboard 当前状态审计报告

## 1. 执行时间

2026-07-06

## 2. Repo Path

`/Users/apple/Documents/同行资本二级市场`

## 3. Branch

`feature/smr-d0-dashboard-audit-blueprint`

## 4. Commit

`ce83e4d`

## 5. 当前 Dashboard 技术栈

### 后端
- **语言**: Python 3
- **Web 框架**: Python 标准库 `http.server`（`BaseHTTPRequestHandler` + `ThreadingHTTPServer`）
- **数据库**: SQLite（`smr.db`）
- **数据格式**: JSON 快照 + Markdown 报告

### 前端
- **技术**: 原生 HTML + CSS + JavaScript
- **渲染方式**: 服务端渲染（Python 字符串拼接 HTML）
- **自动刷新**: 浏览器端 60 秒自动刷新

### 核心文件
- `08_scripts/dashboard/run_control_tower.py`（7047 行）- Dashboard 主服务，HTTP 请求处理，HTML 渲染
- `08_scripts/dashboard/control_tower_service.py` - Dashboard 服务管理（启动/停止/状态检查）
- `08_scripts/lib/smr_dashboard.py`（2359 行）- 数据加载层，从 SQLite 和 JSON 文件聚合状态

## 6. 当前启动方式

```bash
python3 08_scripts/dashboard/run_control_tower.py --host 127.0.0.1 --port 8877
```

可选参数：
- `--refresh-seconds 60` - 浏览器自动刷新间隔（默认 60 秒）
- `--dump-json` - 输出聚合后的状态 JSON 并退出
- `--open-browser` - 启动后自动打开浏览器

启动后访问：`http://127.0.0.1:8877`

状态 API：`http://127.0.0.1:8877/api/state`

健康检查：`http://127.0.0.1:8877/healthz`

## 7. 当前页面清单

### 导航栏可见入口（2 个）
1. **看板** (`/`) - 首页，所有业务信息聚合
2. **审核** (`/review-queue`) - 推荐审核队列

### 实际路由清单（11 个）
| 路由 | 渲染函数 | 实际页面 | 说明 |
|---|---|---|---|
| `/` | `render_home` | 首页看板 | 主入口 |
| `/reports` | `render_home` | 首页看板 | **已合并到首页**，原报告页 |
| `/opportunities` | `render_home` | 首页看板 | **已合并到首页**，原机会页 |
| `/analysis` | `render_home` | 首页看板 | **已合并到首页**，原分析页 |
| `/operations` | `render_home` | 首页看板 | **已合并到首页**，原运维页 |
| `/research` | `render_home` | 首页看板 | **已合并到首页**，原研究页 |
| `/portfolio` | `render_home` | 首页看板 | **已合并到首页**，原组合页 |
| `/risk` | `render_home` | 首页看板 | **已合并到首页**，原风险页 |
| `/capital-flow` | `render_home` | 首页看板 | **已合并到首页**，原资金流页 |
| `/events` | `render_home` | 首页看板 | **已合并到首页**，原事件页 |
| `/review-queue` | `render_review_queue` | 审核队列 | 独立页面 |

### 详情页路由（3 个）
| 路由 | 渲染函数 | 说明 |
|---|---|---|
| `/research/item?ts_code=...` | `render_research_detail_page` | 个股研究详情 |
| `/portfolio/action?id=...` | `render_action_detail_page` | 动作建议详情 |
| `/recommendation/review?id=...` | `render_recommendation_review_page` | 推荐审核详情 |

### 工具路由
| 路由 | 说明 |
|---|---|
| `/api/state` | JSON 格式的完整状态 |
| `/artifact?path=...` | 查看产物文件 |
| `/healthz` | 健康检查 |

## 8. 当前数据入口

### 主数据存储
- **SQLite 数据库**: `01_data/db/smr.db`
  - 主要表：`task_registry_entity_latest`（最新快照）、`task_registry_entry`（历史记录）
  - 约 58 种实体类型快照

### 快照实体类型（58 种）
1. `daily_report_candidate` - 日报候选
2. `daily_reporting_snapshot` - 日报快照
3. `market_flow_anomaly_snapshot` - 市场资金流异常
4. `opportunity_radar_snapshot` - 机会雷达
5. `opportunity_lifecycle_snapshot` - 机会生命周期
6. `strategy_evidence_snapshot` - 策略证据
7. `thesis_attack_defense_snapshot` - 攻防推演
8. `paper_trade_watchlist_snapshot` - 纸面观察单
9. `paper_watch_performance_snapshot` - 纸面表现复盘
10. `opportunity_evidence_gap_snapshot` - 机会证据缺口
11. `data_freshness_snapshot` - 数据新鲜度
12. `current_state_snapshot` - 当前作战状态
13. `deep_market_analysis_snapshot` - 深度市场分析
14. `price_range_forecast_snapshot` - 价格区间预测
15. `execution_precheck_snapshot` - 执行预检
16. `strategy_watch_batch` - 策略观察批次
17. `rotation_candidate_snapshot` - 轮动候选
18. `rotation_execution_plan_snapshot` - 轮动执行计划
19. `portfolio_action_memo_snapshot` - 组合动作备忘录
20. `investment_evidence_pack_snapshot` - 投资证据包
21. `investment_research_synthesis_snapshot` - 投资研究综合
22. `investment_report_snapshot` - 投资报告
23. `investment_evidence_gap_task_snapshot` - 投资证据缺口任务
24. `investment_evidence_gap_fetch_snapshot` - 投资证据缺口获取
25. `risk_monitor_snapshot` - 风险监控
26. `trade_risk_decision_snapshot` - 交易风险决策
27. `market_event_snapshot` - 市场事件
28. `event_calendar_snapshot` - 事件日历
29. `upcoming_event_calendar_snapshot` - 即将到来事件
30. `margin_balance_snapshot` - 两融余额
31. `stock_connect_flow_snapshot` - 互联互通资金流
32. `input_source_registry_snapshot` - 输入源注册

### 运行时数据
- **脚本运行日志**: `10_logs/script_runs.jsonl`
- **调度器运行目录**: `10_logs/scheduler/runs/`
- **Markdown 报告**: 各类快照对应的 Markdown 摘要文件

### 状态聚合结构（`build_dashboard_state` 输出）
```
state
├── overview              # 市场概览（交易日期、延迟、池计数、风险计数等）
├── current_state         # 当前作战状态（P0动作、置顶机会、纸面观察、证据缺口等）
├── reporting             # 报告相关（日报、调度面板、外部研报、官方材料等）
├── opportunity_engine    # 机会引擎（雷达、生命周期、证据、攻防、纸面观察等）
├── system_health         # 系统健康（数据新鲜度）
├── deep_analysis         # 深度市场分析
├── analysis_forecast     # 分析预测
├── portfolio_action      # 组合动作
├── risk                  # 风险监控 + 风险决策
├── capital_flow          # 资金流（两融 + 互联互通）
├── events                # 事件相关
├── operations            # 运维（调度器 + 运行日志）
├── research_detail       # 个股详情数据
└── registry_timeline     # 注册时间线
```

## 9. 当前可用能力

### 投研相关能力
- **个股覆盖**: A股、港股、美股多市场覆盖
- **机会挖掘**: 机会雷达、主题雷达、策略证据、攻防推演
- **研究支持**: 投资证据包、研究综合、证据缺口管理
- **风险监控**: 风险监控、交易风险决策、风险预警
- **组合管理**: 组合动作建议、轮动候选、轮动执行计划
- **纸面观察**: 纸面观察单、纸面表现复盘、生命周期跟踪
- **事件跟踪**: 市场事件、事件日历、即将到来事件
- **资金流**: 两融余额、互联互通资金流、资金流异常
- **外部观点**: 公开卖方信号、公开电话会、官方材料、外部研报

### 运维相关能力
- **数据新鲜度监控**: 各数据源新鲜度检查
- **调度器状态**: 自动调度链运行状态
- **脚本运行日志**: 脚本执行历史
- **输入源注册**: 数据源清单

### 审核工作流
- **推荐审核队列**: 待审核的推荐列表
- **推荐审核详情**: 单条推荐的审核操作
- **审核操作**: 通过/驳回/修改建议仓位/添加评论

## 10. 当前主要问题

### 1. 页面结构混乱
- 10 个业务路由全部指向同一个 `render_home` 函数
- 导航栏只保留了"看板"和"审核"两个入口
- 原有多页面架构已坍缩为单页，但信息组织未优化

### 2. 信息密度过高
- 首页堆叠了所有业务模块：风险、动作、纸面观察、机会、报告等
- 缺少分层和优先级区分
- 投研人员需要自己筛选重要信息

### 3. 技术导向而非投研导向
- 大量技术字段和状态码暴露给用户
- 缺少老板视角的"今日重点"摘要
- 术语偏向开发者而非投研人员

### 4. 证据与结论断裂
- 结论（动作建议、机会评级）和证据（研报、公告、新闻）分散在不同模块
- 追溯证据需要跳转多个页面或查看原始文件
- 缺少"结论 → 证据"的清晰链路

### 5. 缺少投研工作台设计
- 没有明确的"待办事项"或"待判断事项"清单
- 人工审核入口较隐蔽
- 研究队列/证据缺口管理分散

### 6. 数据健康状态不直观
- `data_freshness_snapshot` 存在但首页展示不突出
- 缺少投研人员可理解的健康状态摘要
- 偏向工程日志而非业务健康

### 7. 技术栈限制
- 纯 Python 字符串拼接 HTML，维护成本高
- 缺少前端框架，交互能力有限
- 每次刷新都重新聚合全部数据，性能可能有问题

## 11. 保留页面建议

### 核心保留
- **首页看板能力** - 数据聚合和展示的核心逻辑需要保留，但需要重新设计信息架构
- **审核队列** - 人工审核工作流是关键能力，需要保留并优化
- **个股详情页** - 个股深度研究是核心功能
- **动作详情页** - 动作建议的完整证据链展示

### 数据层保留
- **SQLite 快照架构** - 58 种实体快照是宝贵的数据资产
- **`build_dashboard_state` 聚合逻辑** - 数据整合逻辑成熟
- **`smr_dashboard.py` 工具函数** - 数据格式化和简化函数

## 12. 合并页面建议

### 合并方向
- **所有业务首页**（原 10 个路由）→ 重新设计为 5 个投研页面
  - 今日总览（老板摘要）
  - 覆盖池（公司/行业/主题覆盖）
  - 信号流（证据时间线）
  - 研究队列（待深挖主题）
  - 数据健康（关键健康状态）

### 具体合并
- 原"日报 + 调度面板 + 市场概览" → **今日总览**
- 原"机会雷达 + 主题雷达 + 策略观察" → **覆盖池 + 信号流**
- 原"研究 + 证据缺口 + 证据包" → **研究队列**
- 原"风险 + 资金流 + 事件" → 分散到各相关页面
- 原"运维 + 数据新鲜度" → **数据健康**

## 13. 隐藏/废弃页面建议

### 建议隐藏（暂不删除代码，只不展示入口）
- **`/operations` 运维页** - 工程监控，投研人员不需要
- **详细运行日志** - 开发者调试用，不面向投研
- **输入源注册详情** - 技术配置，不面向投研

### 建议废弃
- 原 10 个路由的独立页面概念（已实际废弃，只是代码中还保留路由）
- 过度技术化的状态码展示
- 纯工程日志的聚合展示

## 14. 风险

### 技术风险
- 当前 Dashboard 代码量大（7000+ 行），重构成本高
- 纯 Python 渲染 HTML，未来交互升级需要重写前端
- 数据聚合全量计算，页面增多后性能可能下降

### 业务风险
- 58 种快照实体，部分可能已过时但无人维护
- 证据链完整性依赖 pipeline 稳定性
- 人工审核流程较简单，可能无法满足合规要求

### 数据风险
- SQLite 单文件数据库，并发写入可能有问题
- 运行时数据未纳入版本管理，环境迁移可能丢失
- 数据新鲜度依赖各 pipeline 按时运行

### 边界风险
- 当前 Dashboard 已有买卖建议和目标价相关逻辑，新设计需要严格遵守边界
- 审核流程可能涉及投资决策，需要明确"系统建议 vs 人工决策"的边界
