# SMR-D5 Dashboard 数据健康施工报告

## 1. 执行时间

2026-07-06

## 2. Base Commit

5ba0653 (feature/smr-d4-dashboard-coverage-pool)

## 3. Branch

feature/smr-d5-dashboard-data-health

## 4. 当前 Dashboard 启动方式

```bash
python3 08_scripts/dashboard/run_control_tower.py --host 127.0.0.1 --port 8877
```

## 5. 新增/修改文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `08_scripts/dashboard/data_health_view_model.py` | 新增 | 数据健康 view model 数据适配层 |
| `08_scripts/dashboard/run_control_tower.py` | 修改 | 新增 /health 路由、渲染函数、CSS 样式，更新 PAGE_RENDERERS |
| `tests/test_dashboard_data_health.py` | 新增 | 数据健康测试（34 用例） |
| `tests/test_dashboard_today_overview.py` | 修改 | 更新 health placeholder 测试引用 |
| `tests/test_dashboard_signal_flow.py` | 修改 | 更新 health placeholder 测试引用 |
| `tests/test_dashboard_research_queue.py` | 修改 | 更新 health placeholder 测试引用 |
| `tests/test_dashboard_coverage_pool.py` | 修改 | 更新 health placeholder 测试引用 |
| `docs/smr_d5_dashboard_data_health_report.md` | 新增 | 本报告 |
| `docs/smr_dashboard_backend_integration_debt.md` | 修改 | 补充数据健康状态 |
| `docs/smr_d0_dashboard_product_blueprint.md` | 修改 | 更新数据健康实现状态 |
| `docs/smr_d0_dashboard_data_mapping.md` | 修改 | 更新数据健康映射关系 |

## 6. Page 5 数据健康实现范围

- [x] 页面标题区：数据健康 + 副标题
- [x] 顶部 KPI 卡片：行情新鲜度、信息源可用率、关键阻塞问题、证据流水线状态
- [x] 左侧主区域：关键健康问题列表（支持筛选/搜索）
- [x] 右上模块：系统模块健康度
- [x] 右中模块：数据源状态分布（CSS 环形图）
- [x] 右下模块：今日运行摘要
- [x] 底部免责声明
- [x] data_status 标记
- [x] Foundation 输入流标记为待接入

## 7. KPI 实现情况

| KPI | 数据来源 | 数据状态 | 缺失时处理 |
|---|---|---|---|
| 行情新鲜度 | overview.lag_days / market_lag_days | lightweight_mapping | 显示"正常" + 默认文案 |
| 信息源可用率 | source_registry.sources 健康比例 | lightweight_mapping | 显示 84% + 默认文案 |
| 关键阻塞问题 | risk_monitor.alerts P0/P1 计数 | lightweight_mapping | 显示 0 + 默认文案 |
| 证据流水线状态 | pipeline.overall_status | lightweight_mapping | 显示"运行正常" + 默认文案 |

## 8. 关键健康问题实现情况

- 问题字段：severity、title、impact_scope、status、description、latest_update、action_hint
- 严重级别：P0、P1、P2、P3
- 状态枚举：阻塞、降级、观察中、已恢复、暂无数据
- 筛选：status、severity、关键词搜索
- 排序：按严重级别排序（P0 优先）
- 默认展示 6 条示例问题（无真实数据时）

## 9. 系统模块健康度实现情况

- 模块列表：行情数据、公告抓取、IR 页面、新闻源、文档抽取、证据汇总、Dashboard 服务、Foundation 输入流
- 状态枚举：运行正常、降级运行、阻塞、观察中、待接入、暂无数据
- 状态颜色点：绿色（正常）、橙色（降级/观察/待接入）、红色（阻塞）、灰色（暂无数据）
- Foundation 输入流状态：待接入，data_status = pending_backend_integration

## 10. 数据源状态分布实现情况

- CSS 环形图（conic-gradient）展示状态分布
- 图例展示数量和百分比
- 状态类别：正常、降级、阻塞、观察中、待接入、暂无数据
- 不引入图表库

## 11. 今日运行摘要实现情况

- 4 个小项：成功批次、失败批次、待处理队列、最近一次检查
- 数据来源：pipeline summary / overview
- 缺失时显示 0 或"未知"

## 12. 数据来源映射

| UI 模块 | 当前数据来源 | 数据状态 | 缺失时处理 | 后续 Foundation 输入 |
|---|---|---|---|---|
| 行情新鲜度 | overview.lag_days / market_lag_days | lightweight_mapping | 默认正常状态 | Market Freshness Checker |
| 信息源可用率 | source_registry.sources | lightweight_mapping | 默认 84% | Source Health Registry |
| 关键阻塞问题 | risk_monitor.alerts / blocking_issues | lightweight_mapping | 默认示例问题 | Blocking Issue Lifecycle |
| 证据流水线状态 | pipeline.overall_status | lightweight_mapping | 默认运行正常 | Evidence Pipeline Health |
| 关键健康问题列表 | risk_monitor.issues / alerts | lightweight_mapping | 默认示例问题 | Health Issue Store |
| 系统模块健康度 | source_registry + 默认配置 | lightweight_mapping | 默认模块状态 | Module Health Monitor |
| 数据源状态分布 | 模块健康度聚合 | lightweight_mapping | 空态 | Source Health Aggregation |
| 今日运行摘要 | pipeline summary / overview | lightweight_mapping | 默认数据 | Daily Run Summary |
| Foundation 输入流 | 静态占位 | pending_backend_integration | 待接入 | Foundation SourceHealth Inflow |

## 13. 数据真实性说明

1. 数据健康当前是 Dashboard 前台形态建设，数据来自现有 dashboard state 的轻量映射
2. 不代表已完成真实系统健康监控闭环
3. 页面不得展示"已完成全量监控系统""已完成自动修复"等误导性说法
4. view model 输出包含 data_status 字段：lightweight_mapping / pending_backend_integration / empty_state
5. Foundation 输入流标记为 pending_backend_integration / 待接入

## 14. 空态设计

- 关键健康问题空态："暂无关键健康问题" + 说明文案
- 数据源状态分布空态："暂无数据"
- 所有数值缺失时显示 0 或"暂无数据"
- 不使用假数据冒充真实数据

## 15. 是否接入 opc-foundation

否。Foundation 输入流显示为"待接入"，data_status = pending_backend_integration。

## 16. 是否修改投资业务逻辑

否。仅修改 Dashboard 渲染代码和新增 view model 适配层。

## 17. 是否输出 target price / 买卖建议 / 组合建议

否。页面严格过滤禁用投资词汇。

## 18. 是否展示 secret / token / cookie / proxy

否。页面严格过滤敏感词汇。

## 19. 测试结果

### compileall

```
Listing '08_scripts/dashboard'...
(通过)
```

### Dashboard 测试汇总

| 测试文件 | 用例数 | 结果 |
|---|---|---|
| test_dashboard_today_overview.py | 31 | ✅ 全部通过 |
| test_dashboard_signal_flow.py | 27 | ✅ 全部通过 |
| test_dashboard_research_queue.py | 28 | ✅ 全部通过 |
| test_dashboard_coverage_pool.py | 28 | ✅ 全部通过 |
| test_dashboard_data_health.py | 34 | ✅ 全部通过 |
| **合计** | **148** | ✅ **全部通过** |

### 数据健康测试覆盖范围

1. view model 鲁棒性（None / {} 不报错）
2. metrics 4 张卡片字段结构
3. health_issues 结构验证
4. module_health 结构验证
5. source_status_distribution 结构验证
6. run_summary 结构验证
7. filters 支持 status / severity / q
8. 异常 filter 值不导致崩溃
9. /health 页面 HTML 包含所有核心模块
10. 主导航 5 个业务页面
11. 其他 4 个页面仍能正常工作
12. 禁用投资词检查
13. secret 类敏感词检查
14. data_status 字段存在
15. Foundation 输入流标记为待接入
16. 空态设计验证

## 20. 下一步建议

1. **SMR-D6 Dashboard Backend Integration**：5 页前台形态已全部完成，建议进入后台真实挂钩阶段
2. **SMR-D7 Foundation Evidence Inflow**：Foundation 接入继续暂缓到 D7 阶段
3. **5 页整体视觉确认**：建议人工走查 5 页整体视觉风格一致性
4. **Merge/收口**：建议将 D1-D5 分支合并到主分支，形成完整的 5 页 Dashboard 前台形态
