# M5 第一轮安全修剪记录

## 边界

- 日期：2026-07-14
- 分支：`refactor/personal-research-mvp`
- 只处理 tracked 文件；不处理未知 untracked 文件。
- 不触碰 `01_data`、`11_smr_wiki`、研究产物、运行日志或本地凭证。
- 每组文件必须具备引用扫描、近 30 天运行证据检查和独立提交。

## 清单机制修复

在开始移动文件前，先修复了两个会造成误判的问题：

1. 手工审批状态在重新扫描后会被重置。
2. Markdown 反引号路径与链接路径未计入引用关系，导致 runbook 引用被漏报。

修复后，`08_scripts/registry/query_registry.py` 从 DELETE_CANDIDATE 回归 KEEP，未删除。

## 归档组 1：Phase 早期部署与建库生成器

处理方式：FREEZE，移动到 `legacy/phase_bootstrap/`，不删除。

审核结论：以下文件均为 tracked 文件；正式代码引用数为 0；近 30 天成功运行数为 0；不在 scheduler、API、`smr_app` 或前台注册表中。它们仍包含历史建库、目录初始化和脚本生成逻辑，因此保留只读归档。

- `deploy_phase2.py`
- `deploy_phase34.py`
- `deploy_phase5.py`
- `smr_phase0_db.py`
- `smr_phase0_dirs.py`
- `smr_phase0_verify.py`
- `smr_phase0_verify2.py`
- `smr_phase0_workspaces.py`

替代路径：

- 数据库结构：`migrations/`
- 当前工作流：`smr_app/workflows/`
- 运行时与适配器：`smr_app/runtime/`、`smr_app/adapters/`
- 日常启动与验证：`api/server.js`、`scripts/check.ps1`

回滚方式：单独回滚归档提交即可恢复原路径。

## 删除记录

本批没有删除 tracked 文件。

## 默认测试边界

`scripts/check.ps1 -Full` 现在明确运行：

- smoke tests
- runtime tests
- 四条 workflow fixture tests
- Express API tests
- React UI tests
- manifest 一致性校验

历史 Phase tests 不进入默认发现范围，只在归档或删除对应 Phase 代码前按组手工运行。

## 归档组 2：Phase 136–140 静态 runner 与契约测试

处理方式：FREEZE，移动到 `legacy/phase_contracts/`，不删除。

审核结论：

- 5 个 runner 与 5 个测试均为 tracked 文件。
- 正式引用数均为 0，近 30 天成功运行数均为 0。
- Phase 141–149 仍有引用，已从本组排除并继续 KEEP。
- 归档前手工运行 146 项 Phase 136–140 legacy tests，全部通过。
- runner 仅组合 `08_scripts/lib/smr_phase136_*` 至 `smr_phase140_*` 的静态契约输出；当前四条工作流已由 `smr_app/workflows/` 接管。

归档 runner：

- `run_phase136_deep_dive_workflow_pipeline.py`
- `run_phase137_deep_dive_execution_pipeline.py`
- `run_phase138_thesis_library_pipeline.py`
- `run_phase139_scheduled_local_delivery.py`
- `run_phase140_system_hardening.py`

归档测试：

- `test_phase136_all.py`
- `test_phase137_all.py`
- `test_phase138_all.py`
- `test_phase139_all.py`
- `test_phase140_all.py`

替代路径：`smr_app/workflows/`、`tests/workflows/`、`scripts/check.ps1 -Full`。

## 归档组 3：Phase 127、129–135 静态 runner 与契约测试

处理方式：FREEZE，移动到 `legacy/phase_contracts/`，不删除。

审核结论：

- 最初审核 Phase 127–135 共 9 个 runner 与 9 个测试；正式引用数均为 0，近 30 天成功运行数均为 0。
- scheduler、正式 API、`smr_app`、前台入口和工作流注册表均未调用这些 runner；底层 `08_scripts/lib/smr_phase*` 模块与配置文件继续保留。
- 原路径首次运行 316 项测试时，Phase 128 的 `pending_network_after <= pending_network_before` 既有断言失败（实际为 `13 <= 12`），因此 Phase 128 runner 与测试从本组排除并原地保留。
- 最终归档范围为 Phase 127、129–135，共 8 个 runner 与 8 个测试。
- 归档前、归档后均运行 277 项对应 legacy tests，全部通过。
- 归档后的 Phase 127、134、135 runner 已分别完成 dry-run，契约输出与安全 guard 正常。

归档 runner：

- `run_phase127_mainline_closeout.py`
- `run_phase129_official_source_fallback_pipeline.py`
- `run_phase130_cninfo_resolution_pipeline.py`
- `run_phase131_alternative_source_integration_pipeline.py`
- `run_phase132_valuation_hardening_pipeline.py`
- `run_phase133_seasonal_analytics_pipeline.py`
- `run_phase134_personal_research_console_pipeline.py`
- `run_phase135_owner_feedback_integration.py`

归档测试：

- `test_phase127_all.py`
- `test_phase129_all.py`
- `test_phase130_all.py`
- `test_phase131_all.py`
- `test_phase132_all.py`
- `test_phase133_all.py`
- `test_phase134_all.py`
- `test_phase135_all.py`

排除项：`run_phase128_external_source_probe_pipeline.py` 与 `test_phase128_all.py`，待历史断言单独审查后再决定是否归档。

替代路径：当前研究控制台由 `src/app/ResearchWorkbench.tsx` 承载，正式工作流由 `smr_app/workflows/` 与 `tests/workflows/` 承载。

## 审计组 4：生成物、临时文件与大型重复入口

处理方式：修正清单，不删除、不移动。

审核结论：

- 11 个 GENERATED 对象均为未跟踪的本地数据库或开发日志，按边界不处理。
- 52 个 DELETE_CANDIDATE 均为已经不存在的旧临时文件记录；当前没有 present、tracked 的删除候选。
- `api/server.js` 已完成拆分，当前仅 20 行、666 字节，继续作为正式 API 启动入口；旧分类规则无条件将其标为 CONSOLIDATE，现已改为仅对大于等于 100 KB 的源码标记 CONSOLIDATE。
- `08_scripts/dashboard/run_control_tower.py` 与 `08_scripts/lib/smr_dashboard.py` 仍由 `control_tower_service.py` 和 `09_runbooks/smr-control-tower.md` 引用；结合经典前台保留边界，本批继续保留，不做孤立移动。
- 新增分类回归测试，保证小型 API bootstrap 为 KEEP，而旧式大型单文件仍为 CONSOLIDATE。

本组没有删除 tracked 文件。
