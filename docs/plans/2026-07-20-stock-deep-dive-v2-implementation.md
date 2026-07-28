# 个股深度研究 V2 实施计划

### 任务 1：数据标准化与隔离

- 输出：`smr_app/research/normalization.py`
- 测试：正常快照、报告期缺失、单位归一、跨字段冲突、异常估值。

### 任务 2：Research Packet v2

- 输出：`smr_app/research/stock_packet.py`
- 测试：证据闭包、数据质量、隔离字段、缺口和 readiness。

### 任务 3：接入受治理工作流

- 输出：`stock_deep_dive` 新增标准化与 Packet 阶段，持久化 JSON artifact。
- 测试：A/H/US fixture、缺失数据、非法代码、artifact 恢复。

### 任务 4：确定性 Claim Compiler

- 输出：`smr_app/research/claim_compiler.py`；事实、变化、预期差边界、催化、风险、下一步调查的结构化 claims。
- 测试：`tests/workflows/test_stock_claim_compiler_v2.py` 覆盖每条 claim 引用闭包、禁止结论、缺失项不外推。

### 任务 5：报告编译器与质量门

- 输出：`smr_app/research/quality_gate.py`、`smr_app/research/report_compiler.py`；从 Packet 重建 Markdown；可选模型只能改写已批准 claims。
- 测试：零无依据陈述、零隔离字段泄漏、报告状态与 Packet 一致。

### 任务 6：聊天入口收敛

- 输出：`api/services/governed-workflow-runner.js` 让 `stock_deep_analysis` 调用同一权威内核，不再维护第二套研究逻辑；本地启动时通过 `SMR_SOURCE_DB_PATH` 将工作流控制库与真实研究库明确分离。
- 测试：`tests/api/governed-stock-chat.test.js`、浏览器启动、执行、刷新恢复、审计 artifact。

### 任务 7：真实评测集

- 输出：至少 10 只代表性股票的固定评测清单和评分结果。
- 测试：事实错误 0、无证据结论 0、引用覆盖 100%、脏字段泄漏 0。
- 状态：已完成（2026-07-21）。固定覆盖 4 只 A 股、2 只港股、4 只美股，并保留无基本面数据、字段冲突、证据闭环失败和二手噪声等非理想样本。
- 复现：`.venv\\Scripts\\python.exe tools\\evaluate_stock_deep_dive_v2.py --source-db ..\\th_capital_stock\\01_data\\db\\smr.db --fail-on-quality`。
- 结果：10/10 质量控制通过，平均 100 分；可检测事实完整性错误 0、无依据方向性结论 0、隔离字段泄漏 0、引用覆盖 100%。数据就绪度单独披露为研究就绪 0、证据有限 9、暂无法判断 1，不用质量控制得分掩盖源数据不足。
