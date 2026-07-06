# SMR-D4 Dashboard 覆盖池施工报告

## 1. 执行时间

2026-07-06

## 2. Base Commit

2add6e6 (feature/smr-d3-dashboard-research-queue)

## 3. Branch

feature/smr-d4-dashboard-coverage-pool

## 4. 当前 Dashboard 启动方式

```bash
python3 08_scripts/dashboard/run_control_tower.py --host 127.0.0.1 --port 8877
```

## 5. 新增/修改文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `08_scripts/dashboard/coverage_pool_view_model.py` | 新增 | 覆盖池 view model 数据适配层 |
| `08_scripts/dashboard/run_control_tower.py` | 修改 | 新增 /coverage 路由、渲染函数、CSS 样式，更新 PAGE_RENDERERS 和 do_GET |
| `tests/test_dashboard_coverage_pool.py` | 新增 | 覆盖池测试（30 用例） |
| `tests/test_dashboard_today_overview.py` | 修改 | 更新 coverage placeholder 测试引用 |
| `tests/test_dashboard_signal_flow.py` | 修改 | 更新 coverage placeholder 测试引用 |
| `tests/test_dashboard_research_queue.py` | 修改 | 更新 coverage placeholder 测试引用 |
| `docs/smr_d4_dashboard_coverage_pool_report.md` | 新增 | 本报告 |
| `docs/smr_dashboard_backend_integration_debt.md` | 修改 | 补充覆盖池状态 |
| `docs/smr_d0_dashboard_product_blueprint.md` | 修改 | 更新覆盖池实现状态 |

## 6. Page 2 覆盖池实现范围

- [x] 页面标题区：覆盖池 + 副标题
- [x] 顶部 KPI 卡片：覆盖公司数、覆盖行业/主题数、高优先级对象、证据完整度
- [x] 左侧主区域：覆盖对象列表（表格形式，支持筛选/搜索/分页）
- [x] 右侧模块：覆盖对象详情（投资关注点、最新关键信号、证据概览、缺失证据、相关主题/关联公司）
- [x] 底部模块：覆盖分布（CSS 环形图 + 图例）
- [x] 底部模块：优先级热区（高优先级对象卡片）
- [x] 底部免责声明
- [x] data_status 标记

## 7. KPI 实现情况

| KPI | 数据来源 | 数据状态 | 缺失时处理 |
|---|---|---|---|
| 覆盖公司数 | strategy_watch + opportunity + risk + evidence_gaps 类型统计 | lightweight_mapping | 显示 0 |
| 覆盖行业/主题数 | daily_report themes + opportunity markets 类型统计 | lightweight_mapping | 显示 0 |
| 高优先级对象 | 筛选 priority=高 的队列项 | lightweight_mapping | 显示 0 |
| 证据完整度 | 各队列项 evidence_completeness 平均值 | lightweight_mapping | 显示 0% |

## 8. 覆盖对象列表实现情况

- 表格字段：名称、类型、最新状态、证据完整度（进度条）、研究优先级、最近更新
- 对象类型：公司、行业、主题
- 状态枚举：跟踪中、重点研究、需补证据、边际改善、风险上升、暂缓、暂无数据
- 优先级枚举：高、中、低
- 默认展示 10 条，支持分页
- 筛选：类型、优先级、状态
- 搜索：关键词搜索

## 9. 覆盖详情实现情况

- 对象名称 + 类型 badge + 状态 badge + 优先级 badge
- 投资关注点：focus_points chip 展示
- 最新关键信号：信号标题 + 日期 + 方向 + 来源
- 证据概览：CSS 环形图 + 已覆盖/部分覆盖/缺失数量
- 缺失证据：缺口标题 + 重要性
- 相关主题 / 关联公司：chip 展示

## 10. 覆盖分布实现情况

- CSS 环形图（conic-gradient）展示公司/主题/行业分布
- 图例展示数量和百分比
- 不引入图表库

## 11. 优先级热区实现情况

- 展示高优先级对象卡片
- 每张卡片：名称、证据完整度、最近更新、进度条
- 最多展示 8 条

## 12. 数据来源映射

| UI 模块 | 当前数据来源 | 数据状态 | 缺失时处理 | 后续 Foundation 输入 |
|---|---|---|---|---|
| 覆盖对象列表 | strategy_watch / opportunity_radar / daily_report / evidence_gaps / risk_monitor | lightweight_mapping | 默认数据填充 | Coverage Object Store |
| 覆盖详情 | 选中队列项的轻量映射 | lightweight_mapping | 空态提示 | EvidencePacket |
| 证据概览 | evidence_count / gap_count 轻量计算 | lightweight_mapping | 0% | Evidence Completeness Engine |
| 缺失证据 | evidence_gaps 或默认占位 | lightweight_mapping | 默认占位 | EvidenceGap |
| 覆盖分布 | 覆盖对象类型统计 | lightweight_mapping | 空态 | Coverage Entity Mapping |
| 优先级热区 | 筛选 priority=高 的对象 | lightweight_mapping | 空态 | RoutePlan |

## 13. 数据真实性说明

1. 覆盖池当前是 Dashboard 前台形态建设，数据来自现有 dashboard state 的轻量映射
2. 不代表已完成真实覆盖池后端闭环
3. 页面未展示"已完成真实覆盖池管理系统""已完成自动覆盖调仓"等误导性说法
4. view model 输出包含 `data_status: "lightweight_mapping"`
5. 默认数据仅在 state 完全缺失时作为 fail-soft 展示，不作为真实数据

## 14. 空态设计

- 覆盖对象列表空态："暂无覆盖对象"提示
- 覆盖详情空态："请选择覆盖对象"提示
- 覆盖分布空态："暂无覆盖分布"提示
- 优先级热区空态："暂无高优先级对象"提示

## 15. 是否接入 opc-foundation

❌ 未接入

## 16. 是否修改投资业务逻辑

❌ 未修改

## 17. 是否输出 target price / 买卖建议 / 组合建议

❌ 未输出

## 18. 测试结果

- compileall：✅ 通过，无语法错误
- today overview tests：✅ 19/19 通过
- signal flow tests：✅ 26/26 通过
- research queue tests：✅ 34/34 通过
- coverage pool tests：✅ 30/30 通过
- dashboard tests：✅ 114/114 通过
- known unrelated failures：无

## 19. 下一步建议

- 进入 Page 5「数据健康」效果图（SMR-D5）
- 继续暂缓 Foundation 接入
- 建议人工确认覆盖池视觉
- 建议 D4/D5 完成后规划 SMR-D6 后台真实挂钩
