# SMR-D6 Dashboard Backend Integration 施工报告

## 1. 执行时间

2026-07-06

## 2. Base Commit

`c56d365` (origin/main)

## 3. Branch

`feature/smr-d6-dashboard-backend-integration`

## 4. 本阶段目标

建立 Dashboard 的**只读真实后台接入层**，让 5 页前台优先使用已有后台真实快照 / 数据库 / 报告 / 状态文件，而不是只依赖默认占位和轻量映射。

## 5. 新增/修改文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `08_scripts/dashboard/backend_data_provider.py` | 新增 | 统一 Backend Data Provider，只读后台状态加载器 |
| `08_scripts/dashboard/run_control_tower.py` | 修改 | route 层统一加载 backend_state，传入各渲染函数 |
| `08_scripts/dashboard/today_overview_view_model.py` | 修改 | 新增 backend_state 参数，优先读取真实后台状态，输出 page_data_status 和 backend_connection_summary |
| `08_scripts/dashboard/coverage_pool_view_model.py` | 修改 | 新增 backend_state 参数，优先读取真实后台状态，输出 page_data_status 和 backend_connection_summary |
| `08_scripts/dashboard/signal_flow_view_model.py` | 修改 | 新增 backend_state 参数，优先读取真实后台状态，输出 page_data_status 和 backend_connection_summary |
| `08_scripts/dashboard/research_queue_view_model.py` | 修改 | 新增 backend_state 参数，优先读取真实后台状态，输出 page_data_status 和 backend_connection_summary |
| `08_scripts/dashboard/data_health_view_model.py` | 修改 | 新增 backend_state 参数，优先读取真实后台状态，输出 page_data_status 和 backend_connection_summary |
| `tests/test_dashboard_backend_data_provider.py` | 新增 | Backend Data Provider 测试（20 用例） |
| `tests/test_dashboard_backend_integration.py` | 新增 | 5 页后台集成测试（53 用例） |
| `docs/smr_d6_dashboard_backend_data_audit.md` | 新增 | 后台数据源审计报告 |
| `docs/smr_d6_dashboard_backend_integration_report.md` | 新增 | 本报告 |

## 6. Backend Data Provider 设计

### 6.1 核心接口

```python
def load_dashboard_backend_state(
    db_path: str | None = None,
    artifact_root: str | None = None,
    allow_missing: bool = True,
) -> dict[str, Any]
```

### 6.2 输出结构

```python
{
    "backend_status": {
        "overall_status": "partial_snapshot",
        "updated_at": "...",
        "sources_checked": 1,
        "sources_available": 1,
        "sources_missing": 0,
        "data_status": "partial_snapshot",
    },
    "overview": {...},
    "coverage": {...},
    "signals": {...},
    "research_queue": {...},
    "health": {...},
    "raw_state": {...},
    "raw_refs": {
        "db_path": "...",
        "artifact_paths": [...],
    },
    "page_statuses": {
        "today_overview": "partial_snapshot",
        "coverage_pool": "lightweight_mapping",
        "signal_flow": "partial_snapshot",
        "research_queue": "lightweight_mapping",
        "data_health": "partial_snapshot",
    },
    "backend_connection_summary": {
        "used_real_sources": [...],
        "used_lightweight_sources": [...],
        "missing_sources": [...],
        "pending_integrations": ["foundation_input_stream"],
    },
    "missing_sources": [...],
    "warnings": [...],
}
```

### 6.3 设计原则

- **只读**：不写入任何状态，不创建数据 artifacts
- **Fail-soft**：缺 DB / 缺文件时不报错，返回 empty/partial 状态
- **不联网**：不访问网络，不调用外部 API
- **不暴露 secret**：不输出任何敏感信息
- **不输出 traceback**：前台页面不显示错误堆栈

## 7. 5 页接入情况

| 页面 | 使用真实源 | data_status | 剩余 lightweight | pending integration |
|---|---|---|---|---|
| 今日总览 | overview / risk / strategy_watch / evidence_gaps | partial_snapshot | 部分默认值 | foundation_input_stream |
| 覆盖池 | strategy_watch / opportunity_engine / evidence_gaps | partial_snapshot | 默认对象、默认主题 | foundation_input_stream |
| 信号流 | risk / evidence_gaps / strategy_watch / daily_report | partial_snapshot | 部分信号来源 | foundation_input_stream |
| 研究队列 | evidence_gaps / strategy_watch / risk | partial_snapshot | 默认研究项、按钮占位 | foundation_input_stream |
| 数据健康 | overview / source_registry / risk / operations | partial_snapshot | 默认健康问题、默认模块状态 | foundation_input_stream |

### 7.1 今日总览

- **真实数据源**：
  - overview.generated_at（更新时间）
  - risk.decision.sell_candidates（风险信号）
  - strategy_watch.top_focus_items（高优先级公司）
  - current_state.evidence_gaps（待判断事项）
  - opportunity_engine.radar（覆盖池异动）
- **data_status**：`partial_snapshot`（DB 可用时）/ `lightweight_mapping`（无 DB 时）
- **page_data_status**：自动从 backend_state.page_statuses 读取
- **backend_connection_summary**：包含 used_real_sources / used_lightweight_sources / missing_sources / pending_integrations

### 7.2 覆盖池

- **真实数据源**：
  - strategy_watch.top_focus_items（重点关注对象）
  - opportunity_engine.radar.markets（机会雷达对象）
  - daily_report.themes（日报主题）
  - risk.decision.sell_candidates（风险对象）
  - current_state.evidence_gaps（证据缺口对象）
- **data_status**：`partial_snapshot`（有真实数据时）/ `lightweight_mapping`（默认回退）
- **注意**：覆盖对象列表仍有默认值回退，但标记了正确的 data_status

### 7.3 信号流

- **真实数据源**：
  - risk.decision.sell_candidates（风险信号）
  - current_state.evidence_gaps（证据缺口信号）
  - strategy_watch.top_focus_items（策略关注信号）
  - risk.monitor.alerts（风险监控告警）
  - daily_report.highlights（日报摘要）
- **data_status**：`partial_snapshot`
- **信号来源分布**：根据真实信号类型聚合

### 7.4 研究队列

- **真实数据源**：
  - current_state.evidence_gaps（待补证据事项）
  - strategy_watch.top_focus_items（重点研究项）
  - risk.decision.sell_candidates（风险复核项）
  - daily_report.highlights（日报研究项）
- **data_status**：`partial_snapshot`
- **重要**：研究队列按钮（通过 / 补证据 / 暂缓 / 驳回）仍为前台占位，不写入真实后台
- **pending_backend_integration**：research_task_store（待后续阶段）

### 7.5 数据健康

- **真实数据源**：
  - overview.lag_days / market_lag_days（行情新鲜度）
  - source_registry.sources（信息源可用率）
  - risk.monitor.alerts / blocking_issues（关键阻塞问题）
  - operations.scheduler.today_status_counts（流水线状态）
- **data_status**：`partial_snapshot`
- **Foundation 输入流**：保持 `pending_backend_integration` 状态
- **注意**：默认 84% 可用率等默认值在有真实 source_registry 数据时会被覆盖

## 8. 数据状态变化对比

| 页面 | D5 状态 | D6 状态 | 变化说明 |
|---|---|---|---|
| 今日总览 | lightweight_mapping | partial_snapshot | 接入真实 overview/risk/strategy/evidence_gaps |
| 覆盖池 | lightweight_mapping | partial_snapshot | 接入真实 strategy_watch/opportunity/evidence_gaps |
| 信号流 | lightweight_mapping | partial_snapshot | 接入真实 risk/evidence_gaps/strategy/daily_report |
| 研究队列 | lightweight_mapping | partial_snapshot | 接入真实 evidence_gaps/strategy/risk |
| 数据健康 | lightweight_mapping | partial_snapshot | 接入真实 overview/source_registry/risk/operations |

## 9. lightweight_mapping 剩余项

- 覆盖池默认对象（无真实数据时回退）
- 研究队列按钮（通过/补证据/暂缓/驳回）仍为前台占位
- 数据健康默认健康问题（无真实告警时回退）
- 数据健康默认模块状态（无真实 source_registry 时回退）
- 信号流部分信号时间戳（基于索引推算，非真实时间）

## 10. pending_backend_integration 剩余项

- **Foundation 输入流**：全部 5 页均标记为待接入
- **Research Task Store**：研究队列真实任务状态存储
- **Coverage Object Store**：覆盖对象独立存储
- **写入接口**：所有状态变更写入（D6 是只读）

## 11. 边界确认

| 检查项 | 状态 | 说明 |
|---|---|---|
| 是否接入 opc-foundation | 否 | Foundation 输入流保持 pending_backend_integration |
| 是否调用 Foundation runner | 否 | 未调用 |
| 是否创建 Foundation EvidencePacket | 否 | 未创建 |
| 是否修改投资业务逻辑 | 否 | 仅修改数据适配层和路由层 |
| 是否修改估值模型 | 否 | 未修改 |
| 是否修改预期差模型 | 否 | 未修改 |
| 是否修改组合/仓位/风控/交易信号逻辑 | 否 | 未修改 |
| 是否新增真实审核写入接口 | 否 | 按钮仍为前台占位 |
| 是否新增真实研究任务状态写入 | 否 | 只读 |
| 是否新增交易动作 | 否 | 未新增 |
| 是否联网抓新数据 | 否 | 只读现有 DB |
| 是否调用搜索 API | 否 | 未调用 |
| 是否配置 production | 否 | 本地开发环境 |
| 是否提交 data/ | 否 | data/ 未提交 |
| 是否提交 01_data/db/smr.db | 否 | DB 文件未提交 |
| 是否提交 .env / secrets | 否 | 未提交 |
| 是否打 tag | 否 | 未打 tag |
| 是否输出 target price | 否 | 禁用词检查通过 |
| 是否输出买卖建议 | 否 | 禁用词检查通过 |
| 是否输出组合建议 | 否 | 禁用词检查通过 |
| 是否展示 secret/token/cookie/proxy | 否 | 敏感词检查通过 |

## 12. 测试结果

### 12.1 测试统计

| 测试类型 | 用例数 | 结果 |
|---|---|---|
| compileall | - | PASS |
| 旧 Dashboard 测试 | 148 | PASS |
| Backend Provider 测试 | 20 | PASS |
| Backend Integration 测试 | 33 | PASS |
| **总计** | **201** | **PASS** |

### 12.2 测试覆盖要点

**Backend Provider 测试（20 用例）**：
- load_dashboard_backend_state(None, None) 不报错
- 缺 DB / 缺 artifact 时返回 empty/partial 状态
- provider 输出 backend_status
- provider 不写文件
- provider 不联网
- Foundation 输入流为 pending_backend_integration
- 5 页 page_statuses 完整

**Backend Integration 测试（33 用例）**：
- 今日总览能接收 backend_state
- 覆盖池能接收 backend_state
- 信号流能接收 backend_state
- 研究队列能接收 backend_state
- 数据健康能接收 backend_state
- 每页输出 page_data_status
- 每页输出 backend_connection_summary
- Foundation 输入流仍为 pending_backend_integration
- 研究队列按钮不写真实状态
- 禁用投资词不出现在输出
- secret/token/cookie/proxy 不出现在输出
- DB 缺失时仍返回有效 view model

## 13. Foundation 接入状态

- **状态**：未接入
- **预留接口**：
  - 所有 view model 的 `backend_connection_summary.pending_integrations` 包含 `foundation_input_stream`
  - 数据健康页面 Foundation 输入流模块标记为 `pending_backend_integration`
- **计划接入阶段**：SMR-D7 Foundation Evidence Inflow

## 14. 真实后台闭环状态

- 是否已真实读取后台数据：是（通过 build_dashboard_state 读取 SQLite DB 快照）
- 是否已真实写入后台状态：否（D6 是只读）
- 是否已形成完整业务闭环：否（仅只读展示，无写入）
- 哪些模块仍是只读：全部 5 页均为只读
- 哪些模块仍待 D7/Foundation：Foundation 输入流、真实研究任务流

## 15. 下一步建议

1. **D6.1 深化真实数据源覆盖**（可选）：
   - 增加更多真实字段的映射
   - 细化模块级 data_status 标记
   - 优化默认值回退逻辑

2. **准备 D7 Foundation Evidence Inflow**：
   - 设计 Foundation 输入流数据结构
   - 预留干净的接入接口
   - 准备测试数据和 mock

3. **补充 coverage/research queue 的真实 store**（可选）：
   - 是否需要独立的 coverage object store
   - 是否需要独立的 research task 状态存储

4. **页面视觉优化**（可选）：
   - 在页面上轻量展示 data_status 标记
   - 增加数据源可信度提示
