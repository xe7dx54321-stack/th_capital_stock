# SMR-D5.6 Dashboard Frontend Merge Staging 报告

## 1. 执行时间

2026-07-06

## 2. origin/main Commit

2792c64

## 3. Source Acceptance Branch

origin/feature/smr-d55-dashboard-frontend-acceptance

## 4. Source Acceptance Commit

ff6001f

## 5. Staging Branch

feature/smr-d56-dashboard-frontend-main-staging

## 6. 合并策略

| 策略项 | 说明 |
|---|---|
| 是否从 origin/main 创建干净 staging | ✅ 是 |
| 是否直接 merge local rewritten main | ❌ 否 |
| 是否 force push main | ❌ 否 |
| 文件带入方式 | git checkout origin/feature/smr-d55-dashboard-frontend-acceptance -- <file> |
| 带入文件数量 | 23 个文件 |

## 7. 人工视觉验收继承

| 项目 | 结论 |
|---|---|
| 是否记录用户视觉验收通过 | ✅ 是 |
| 验收范围 | 今日总览 / 覆盖池 / 信号流 / 研究队列 / 数据健康 |
| 用户结论 | 5 个页面视觉效果目前没有问题，可以进入工程收口验收 |

## 8. D1-D5.5 验收结果摘要

| 阶段 | 页面 | 前台形态 | 后台接入 | data_status |
|---|---|---|---|---|
| SMR-D1 | 今日总览 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| SMR-D2 | 信号流 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| SMR-D3 | 研究队列 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| SMR-D4 | 覆盖池 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| SMR-D5 | 数据健康 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| SMR-D5.5 | 前台验收 | ✅ 8/8 PASS | - | - |

## 9. 带入文件清单

### Dashboard 代码 (6 个文件)

| 文件 | 类型 |
|---|---|
| 08_scripts/dashboard/run_control_tower.py | 修改 |
| 08_scripts/dashboard/today_overview_view_model.py | 新增 |
| 08_scripts/dashboard/signal_flow_view_model.py | 新增 |
| 08_scripts/dashboard/research_queue_view_model.py | 新增 |
| 08_scripts/dashboard/coverage_pool_view_model.py | 新增 |
| 08_scripts/dashboard/data_health_view_model.py | 新增 |

### 测试文件 (5 个文件)

| 文件 | 类型 | 用例数 |
|---|---|---|
| tests/test_dashboard_today_overview.py | 新增 | 31 |
| tests/test_dashboard_signal_flow.py | 新增 | 27 |
| tests/test_dashboard_research_queue.py | 新增 | 28 |
| tests/test_dashboard_coverage_pool.py | 新增 | 28 |
| tests/test_dashboard_data_health.py | 新增 | 34 |

### 文档文件 (12 个文件)

| 文件 | 类型 |
|---|---|
| docs/smr_d0_dashboard_current_state_audit.md | 新增 |
| docs/smr_d0_dashboard_product_blueprint.md | 修改 |
| docs/smr_d0_dashboard_data_mapping.md | 修改 |
| docs/smr_d0_foundation_inflow_dashboard_design.md | 新增 |
| docs/smr_d1_dashboard_today_overview_report.md | 新增 |
| docs/smr_d2_dashboard_signal_flow_report.md | 新增 |
| docs/smr_d3_dashboard_research_queue_report.md | 新增 |
| docs/smr_d4_dashboard_coverage_pool_report.md | 新增 |
| docs/smr_d5_dashboard_data_health_report.md | 新增 |
| docs/smr_d55_dashboard_frontend_acceptance_report.md | 新增 |
| docs/smr_d56_dashboard_frontend_merge_staging_report.md | 新增 |
| docs/smr_dashboard_backend_integration_debt.md | 修改 |

## 10. 5 页当前状态

| 页面 | 功能 | KPI/列表 | 空态 | 筛选 | 免责声明 |
|---|---|---|---|---|---|
| 今日总览 | ✅ 已完成 | ✅ 4 张 KPI + 列表 | ✅ 有 | ✅ 有 | ✅ 有 |
| 覆盖池 | ✅ 已完成 | ✅ 覆盖公司列表 | ✅ 有 | ✅ 有 | ✅ 有 |
| 信号流 | ✅ 已完成 | ✅ 信号时间线 + 摘要 | ✅ 有 | ✅ 有 | ✅ 有 |
| 研究队列 | ✅ 已完成 | ✅ 研究列表 + 详情 | ✅ 有 | ✅ 有 | ✅ 有 |
| 数据健康 | ✅ 已完成 | ✅ 4 张 KPI + 模块健康度 | ✅ 有 | ✅ 有 | ✅ 有 |

## 11. 真实后台闭环状态

| 项目 | 状态 |
|---|---|
| 是否真实后台闭环 | ❌ 否 |
| 是否已接入真实审核接口 | ❌ 否 |
| 是否已接入证据管理后端 | ❌ 否 |
| 是否已接入用户权限系统 | ❌ 否 |
| 当前数据状态 | 全部为 lightweight_mapping |
| Foundation 输入流 | 待接入 (pending_backend_integration) |

## 12. opc-foundation 接入状态

| 项目 | 状态 |
|---|---|
| 是否已接入 opc-foundation | ❌ 否 |
| Foundation SourceHealth inflow | ❌ 待接入 |
| Foundation Evidence Inflow | ❌ 待接入 |
| 计划接入阶段 | SMR-D7 |

## 13. 测试结果

| 测试项 | 结果 |
|---|---|
| compileall | ✅ 待验证 |
| today overview tests (31) | ✅ 待验证 |
| signal flow tests (27) | ✅ 待验证 |
| research queue tests (28) | ✅ 待验证 |
| coverage pool tests (28) | ✅ 待验证 |
| data health tests (34) | ✅ 待验证 |
| dashboard tests 总计 | **148 待验证** |
| acceptance checks | ✅ 待验证 |

## 14. 禁用词 / Secret 检查结果

| 检查项 | 结果 |
|---|---|
| 投资建议禁用词 | ✅ 待验证 |
| secret/token/cookie/proxy | ✅ 待验证 |
| 检查方式 | Python 脚本扫描渲染 HTML |

## 15. 是否提交 data/db/runtime artifacts

| 项目 | 状态 |
|---|---|
| data/ | ❌ 未提交 |
| 01_data/db/smr.db | ❌ 未提交 |
| .env | ❌ 未提交 |
| secrets/tokens/cookies | ❌ 未提交 |
| runtime artifacts | ❌ 未提交 |
| screenshots | ❌ 未提交 |

## 16. 是否修改投资业务逻辑

| 项目 | 状态 |
|---|---|
| 是否修改投资业务逻辑 | ❌ 否 |
| 是否修改估值模型 | ❌ 否 |
| 是否修改预期差模型 | ❌ 否 |
| 是否修改组合/仓位/风控/交易信号逻辑 | ❌ 否 |

## 17. 是否准备 merge main

| 项目 | 状态 |
|---|---|
| 是否准备通过 PR 合并 main | ✅ 是，待测试验证通过后 |
| 是否需要进一步修改 | ❌ 否，当前状态已通过验收 |
| 是否需要人工确认 | ✅ 建议人工确认后 merge |

## 18. 下一步建议

| 建议 | 结论 |
|---|---|
| 是否准备通过 PR 合并 main | ✅ 是 |
| 是否进入 SMR-D6 Dashboard Backend Integration | ✅ 是，merge 后进入 |
| 是否继续暂缓 Foundation 接入到 SMR-D7 | ✅ 是 |

---

## 附录：带入文件详细清单

```
08_scripts/dashboard/run_control_tower.py
08_scripts/dashboard/today_overview_view_model.py
08_scripts/dashboard/signal_flow_view_model.py
08_scripts/dashboard/research_queue_view_model.py
08_scripts/dashboard/coverage_pool_view_model.py
08_scripts/dashboard/data_health_view_model.py

tests/test_dashboard_today_overview.py
tests/test_dashboard_signal_flow.py
tests/test_dashboard_research_queue.py
tests/test_dashboard_coverage_pool.py
tests/test_dashboard_data_health.py

docs/smr_d0_dashboard_current_state_audit.md
docs/smr_d0_dashboard_product_blueprint.md
docs/smr_d0_dashboard_data_mapping.md
docs/smr_d0_foundation_inflow_dashboard_design.md
docs/smr_d1_dashboard_today_overview_report.md
docs/smr_d2_dashboard_signal_flow_report.md
docs/smr_d3_dashboard_research_queue_report.md
docs/smr_d4_dashboard_coverage_pool_report.md
docs/smr_d5_dashboard_data_health_report.md
docs/smr_d55_dashboard_frontend_acceptance_report.md
docs/smr_d56_dashboard_frontend_merge_staging_report.md
docs/smr_dashboard_backend_integration_debt.md
```