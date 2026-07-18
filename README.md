# SMR 个人研究工作台

SMR（Structured Market Research）是一套本地优先的个人二级市场研究系统，覆盖数据采集、研究证据、估值、风险、报告、纸面组合与工作流编排。它只用于研究辅助和模拟复盘，不连接券商，也不会创建真实交易。

## 一、安装

环境要求：Windows 10/11、Python 3.11+、Node.js 20+、PowerShell 5.1+。

在仓库根目录执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm ci
```

首次使用或排障时先运行只读诊断：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\doctor.ps1
```

诊断脚本只检查环境、目录和数据库，不修改研究数据，也不会输出任何凭证值。iFinD 凭证只通过当前用户的环境变量 `IFIND_REFRESH_TOKEN` 提供，严禁写入源码、文档或日志。

## 二、启动

一条命令启动 API 和前台控制台：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1
```

脚本会自动检查环境、执行尚未应用的数据库迁移，并等待两个服务通过健康检查。默认地址：

- 前台控制台：`http://127.0.0.1:5173/workbench`
- API 健康检查：`http://127.0.0.1:3000/api/health`
- 开发日志：`10_logs/dev/`

停止本项目启动的服务：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-local.ps1
```

停止脚本会核对进程归属，只停止由当前仓库启动并记录的进程，不做全局端口清理。

## 三、每日使用

建议按以下顺序使用：

1. 运行 `doctor.ps1`，确认 Python、Node、数据库和端口状态。
2. 运行 `start-local.ps1`，打开工作台。
3. 在工作台完成数据更新、研究、风险检查与复盘。
4. 当天研究结束后运行 `backup-local.ps1`。
5. 运行 `stop-local.ps1` 安全停止服务。

开发完成后执行快速检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

等价简写为 `npm run check:quick`。

准备提交或修改数据库、工作流后执行完整检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1 -Full
```

等价简写为 `npm run check:full`。

## 四、故障恢复

先停止服务并重新诊断：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-local.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\doctor.ps1
```

若默认端口被其他程序占用，可使用独立端口启动：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1 -ApiPort 3100 -UiPort 5273
```

若怀疑数据库损坏，先保留原文件，不要覆盖；对最近备份做完整性校验，再用备用端口进行只读式恢复验证：

```powershell
.\.venv\Scripts\python.exe .\scripts\local_db_ops.py verify --db .\01_data\backups\smr-backup-YYYYMMDD-HHMMSS.db
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1 -DatabasePath .\01_data\backups\smr-backup-YYYYMMDD-HHMMSS.db -ApiPort 3100 -UiPort 5273
```

确认页面和关键数据正常后停止备用实例，再按照[本地运行与恢复手册](09_runbooks/smr-local-operations.md)执行正式恢复。

## 五、备份

手动创建经过 SQLite 在线备份与完整性校验的快照：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backup-local.ps1
```

备份默认写入 `01_data/backups/`，仅清理该目录内命名符合规则且超过 14 天的历史快照。备份文件、运行数据库、日志和临时运行状态均不进入 Git。

每日自动备份、恢复确认清单、备用端口和日志定位方法详见[本地运行与恢复手册](09_runbooks/smr-local-operations.md)。

## 仓库入口

- React 前台：`src/`
- Express API：`api/`
- Python 业务能力：`08_scripts/` 与 `smr_app/`
- 本地数据库：`01_data/db/smr.db`
- 运维脚本：`scripts/`
- 仓库资产清单：`legacy_manifest/`

安全底线：真实研究数据不通过 Git 迁移；未跟踪文件先进入资产清单分类；高判断研究对象必须经过人工批准，才能进入正式记忆或决策层。

## 六、当前功能状态（2026-07-18）

本工作台已从"数据采集 + 静态看板"演进为"自然语言驱动的多轮投研 Agent"。下列能力均已落地并通过端到端测试。

### 6.1 Agent 工作流引擎（核心）

- **LLM 意图识别**：用户自然语言输入（如"扫描一下今天的投资机会"）经 `api/services/intent-engine.js` 解析为结构化任务，无需穷举命令。
- **动态流程编排**：根据意图自动组装工具链，支持 9 类预设任务（机会扫描、每日简报、风险分析、深度分析、美股映射、组合回顾等）。
- **多轮对话上下文**：前端 `chatHistory` 全链路传递至 LLM messages，支持"继续输出"、"接着说"等追问。
- **工具集**：涨幅榜/跌幅榜/放量异动/价格异动/估值极端/最新新闻/股票池快照/美股数据/映射分析 等 20+ 工具。
- **容错**：LLM 返回 JSON 含 markdown 标记时自动清洗；解析失败时按关键词回退匹配（扫描/复盘/简报/风险等）。

### 6.2 会话管理（1:1 复现 Codex）

- **三层存储**：`sessions/*.jsonl`（消息流）+ `state_5.sqlite` threads 表（索引）+ `session_index.jsonl`（轻量索引）。
- **CRUD 操作**：创建（UUID）、列表（置顶优先→时间倒序）、切换（resume）、置顶（pinned）、归档（archived）、删除（purge）。
- **持久化**：刷新页面后历史会话不丢失，自动恢复最近会话。
- **实现**：`api/services/session-service.js` + `src/features/chat/SessionSidebar.tsx`。

### 6.3 聊天界面（双状态）

- **空状态欢迎页**：无对话时显示"今天想分析点什么？" + 4 个推荐任务卡片（今日复盘/涨跌幅归因/机会雷达/市场新闻）。
- **工作状态聊天页**：有对话时切换为消息流 + 执行过程 + Markdown 报告渲染。
- **侧边栏**：左侧会话列表（新建 + 历史 + 置顶 + 归档分组），中间工作区，已移除运行档案与研究产物面板。

### 6.4 实时行情数据服务

数据源优先级与覆盖范围：

| 数据类型 | 主数据源 | 备用 | 缓存 |
|---------|---------|------|------|
| 大盘指数（上证/深证/创业板/科创50/沪深300等 8 只） | 新浪 `hq.sinajs.cn`（GBK 编码） | - | 5 分钟 |
| 涨幅榜/跌幅榜 | 新浪 `vip.stock.finance.sina.com.cn` | 东方财富 `push2.eastmoney.com` | 2 分钟 |
| 放量异动 | 基于涨幅榜筛选（量比 / 换手率） | - | - |
| 单股实时行情 | 腾讯 `qt.gtimg.cn` | 东方财富 | 5 分钟 |
| 估值极端标的 | 本地数据库 `valuation_snapshot` 表 | - | - |

**已修复的关键 Bug**：
- 新浪大盘指数返回 GBK 编码，用 `TextDecoder("gbk")` 解码（否则指数名称变乱码）。
- 大盘指数成交额在 `parts[9]`（单位：元），不是 `parts[8]`（成交量手数）。
- `valuation_snapshot` 表查询：字段重命名 `ticker → ts_code`、子查询去重（避免同一股票 66 条历史快照被当成 66 只）、过滤 null、`historical_percentile` 是 0-1 小数（阈值用 0.2/0.8 而非 20/80）。
- 估值数据为 null 时明确告知 LLM "数据缺失，不得编造"，防止生成"腾讯 PE 17.9 分位 0.05%"等假数据。

### 6.5 LLM 服务

- **模型**：MiniMax-M2.7（`12_smr_agents/model_runtime/model_profiles.json` 配置），`anthropic_messages` 格式。
- **maxTokens**：默认 16000（从 8000 提升，避免长报告截断）。
- **system prompt 分任务类型**：daily_brief / opportunity_scan / risk_analysis / chat 等各有专用 prompt。
- **可沉淀记忆提取**：报告生成后自动提取结构化记忆，按章节标题智能分类（不再全是"分析结论"）。

### 6.6 已知遗留问题

- 记忆提取分类精度仍有优化空间（部分章节标题被统一归为"分析结论"）。
- `daily_bar` 表在 MVP 数据库中不存在，本地 fallback 路径仅在实时 API 失败时触发报错（不影响主流程）。
- 部分调试脚本（`api/debug_sources*.js`、`api/test_*.js`）尚未清理，后续可在下一次整理时删除。

## 七、快速验证

启动后端后，可运行端到端测试脚本验证主流程：

```powershell
# 启动服务
npm run start

# 另开终端，运行扫描测试
node scripts/test-e2e-scan.js

# 验证涨跌幅数据源
node scripts/test-rank-data.js
```

预期结果：`taskType = opportunity_scan`，9/9 步骤全部执行，报告包含正确的中文指数名称、合理成交额（亿元）、未编造的估值数据。
