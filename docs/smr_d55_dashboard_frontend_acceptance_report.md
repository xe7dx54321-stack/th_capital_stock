# SMR-D5.5 Dashboard 前台验收与收口报告

## 1. 执行时间

2026-07-06

## 2. Base Branch

feature/smr-d5-dashboard-data-health

## 3. Base Commit

83ac0e0

## 4. Acceptance Branch

feature/smr-d55-dashboard-frontend-acceptance

## 5. 人工视觉验收结论

| 项目 | 结论 |
|---|---|
| 是否通过 | ✅ 通过 |
| 验收人 | 用户 |
| 验收方式 | 用户本地查看 5 个 Dashboard 页面 |
| 验收范围 | 今日总览 / 覆盖池 / 信号流 / 研究队列 / 数据健康 |

**用户结论**：5 个页面视觉效果目前没有问题，可以进入工程收口验收。

**重要说明**：
- 人工视觉验收通过 ≠ 真实后台闭环完成
- 人工视觉验收通过 ≠ Foundation 接入完成

## 6. 5 页 Smoke Test 结果

| page | URL | HTTP status | active nav | result |
|---|---|---:|---|---|
| 今日总览 | / | ✅ 200 | ✅ 今日总览 active | ✅ PASS |
| 覆盖池 | /coverage | ✅ 200 | ✅ 覆盖池 active | ✅ PASS |
| 信号流 | /signals | ✅ 200 | ✅ 信号流 active | ✅ PASS |
| 研究队列 | /research | ✅ 200 | ✅ 研究队列 active | ✅ PASS |
| 数据健康 | /health | ✅ 200 | ✅ 数据健康 active | ✅ PASS |

**Query Parameters Fail-Soft**：✅ 异常参数不导致 500

## 7. 导航一致性

| 检查项 | 结果 |
|---|---|
| 主导航是否只有 5 页 | ✅ 是，仅：今日总览/覆盖池/信号流/研究队列/数据健康 |
| 是否存在旧运维导航 | ✅ 否 |
| 每页 active 状态是否正确 | ✅ 是，当前页面对应导航项高亮 |

## 8. 禁用词与敏感词检查

| 检查项 | 结果 |
|---|---|
| 投资建议禁用词是否出现 | ✅ 否，未检测到：target price/目标价/买入/卖出/建仓/仓位建议/组合建议 |
| secret/token/cookie/proxy 是否出现 | ✅ 否，未检测到敏感词 |
| 检查方式 | Python 脚本扫描 5 页渲染 HTML |

## 9. data_status / placeholder 检查

| 页面 | data_status | Foundation 状态 |
|---|---|---|
| 今日总览 | lightweight_mapping | - |
| 覆盖池 | lightweight_mapping | - |
| 信号流 | lightweight_mapping | - |
| 研究队列 | lightweight_mapping | - |
| 数据健康 | lightweight_mapping | Foundation 输入流: 待接入, pending_backend_integration |

**默认值是否明确为 lightweight/default/pending**：✅ 是，所有 view model 输出包含 `data_status: lightweight_mapping`

## 10. 当前真实后台挂钩状态

| 页面 | 前台形态 | 后台接入 | data_status |
|---|---|---|---|
| 今日总览 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| 覆盖池 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| 信号流 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| 研究队列 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |
| 数据健康 | ✅ 已完成 | ❌ 未接入 | lightweight_mapping |

**是否已真实后台闭环**：❌ 否，5 页均为轻量映射，未完成真实后台闭环
**是否已接入 opc-foundation**：❌ 否，Foundation 输入流标记为待接入

## 11. 测试结果

| 测试项 | 结果 |
|---|---|
| compileall | ✅ 通过 |
| today overview tests (31) | ✅ 全部通过 |
| signal flow tests (27) | ✅ 全部通过 |
| research queue tests (28) | ✅ 全部通过 |
| coverage pool tests (28) | ✅ 全部通过 |
| data health tests (34) | ✅ 全部通过 |
| dashboard tests 总计 | **148 passed** |
| acceptance checks | ✅ 8/8 PASS |
| known unrelated failures | 无 |

## 12. 边界确认

| 边界项 | 结果 |
|---|---|
| 是否修改投资业务逻辑 | ❌ 否 |
| 是否接入 opc-foundation | ❌ 否 |
| 是否真实联网 | ❌ 否 |
| 是否调用搜索 API | ❌ 否 |
| 是否写入真实后台状态 | ❌ 否 |
| 是否配置 production | ❌ 否 |
| 是否提交 data/db/runtime artifacts | ❌ 否 |
| 是否输出 target price | ❌ 否 |
| 是否输出买卖建议 | ❌ 否 |
| 是否输出组合建议 | ❌ 否 |
| 是否展示 secret/token/cookie/proxy | ❌ 否 |
| 是否打 tag | ❌ 否 |

## 13. 本阶段修复项

验收过程中发现并修复以下问题：

1. **免责声明补充**：今日总览、覆盖池、信号流、研究队列补充"不提供任何投资建议"文案
2. **data_status 补充**：今日总览和信号流 view model 补充 `data_status: lightweight_mapping` 字段
3. **CSS 样式补充**：新增 `.today-disclaimer` 样式

## 14. 新增/修改文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `08_scripts/dashboard/today_overview_view_model.py` | 修改 | 补充 data_status 字段 |
| `08_scripts/dashboard/signal_flow_view_model.py` | 修改 | 补充 data_status 字段 |
| `08_scripts/dashboard/run_control_tower.py` | 修改 | 补充免责声明和 CSS 样式 |
| `docs/smr_d55_dashboard_frontend_acceptance_report.md` | 新增 | 本验收报告 |

## 15. Commit / Push

- **branch commit**: 待提交
- **origin branch**: feature/smr-d55-dashboard-frontend-acceptance
- **PR link**: 待创建
- **git status**: 4 files modified, 1 file new

## 16. 下一步建议

| 建议 | 结论 |
|---|---|
| 是否准备 merge 到主分支 | ✅ 是，验收通过后可合并 |
| 是否进入 SMR-D6 Dashboard Backend Integration | ✅ 是，5 页前台形态已全部完成 |
| 是否继续暂缓 Foundation 接入到 SMR-D7 | ✅ 是，Foundation 接入安排在 SMR-D7 |

---

## 附录：验收检查详细结果

### A. 禁用投资词汇检查

扫描 5 页 HTML，以下词汇均未出现：
- target price / 目标价
- 买入 / 卖出 / 建仓
- 仓位建议 / 组合建议
- position_size / trade_signal / expected_return / valuation_upside / portfolio_action

### B. 禁用敏感词汇检查

扫描 5 页 HTML，以下词汇均未出现：
- AIza / api_key / secret / token
- cookie / proxy_url / password / private_key

### C. 免责声明检查

| 页面 | 免责声明文案 |
|---|---|
| 今日总览 | 系统仅展示证据与信号，不直接给出投资建议。不提供任何投资建议。 |
| 覆盖池 | 系统展示覆盖状态与证据完整度，不直接给出投资建议。不提供任何投资建议。 |
| 信号流 | 系统仅展示证据与信号，不直接给出投资建议。不提供任何投资建议。 |
| 研究队列 | 系统仅组织研究证据与待办，不直接给出投资建议。不提供任何投资建议。 |
| 数据健康 | 数据健康页面用于观察投研系统的运行状态与数据质量，帮助及时发现并定位问题，保障研究工作的可靠性与连续性。不提供任何投资建议。 |

### D. Foundation 输入流状态

- **模块名称**: Foundation 输入流
- **状态**: 待接入
- **data_status**: pending_backend_integration
- **说明**: 当前未接入 opc-foundation，计划在 SMR-D7 阶段完成