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
