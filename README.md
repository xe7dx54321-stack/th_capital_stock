# SMR Personal Research Workbench

SMR（Structured Market Research）是一套本地优先的个人二级市场研究系统。当前仓库包含行情与公告采集、因子、基本面、估值、证据图、研究报告、paper portfolio、风险、Agent handoff，以及正在建设的个人研究工作台。

本项目只用于研究辅助和纸面复盘，不连接券商、不创建真实交易。

## 当前开发入口

- 实施计划：`docs/plans/2026-07-13-personal-research-workbench-mvp.md`
- Python 业务能力：`08_scripts/`
- 本地 API：`api/server.js`
- React 前端：`src/`
- SQLite：`01_data/db/smr.db`，运行数据不进入 Git
- 仓库资产清单：`legacy_manifest/`

## 环境要求

- Windows 10/11
- Python 3.11+
- Node.js 20+
- PowerShell 5.1+

不要依赖全局 Python 包或全局 TypeScript。Python 包安装到 `.venv`，Node 包由 `npm ci` 按 lockfile 安装。

## 首次安装

在仓库根目录执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm ci
```

如果机器没有 `py`，可以用已安装的 Python 3.11+ 完整路径创建 `.venv`。

### 初始化本地数据库

新环境没有运行数据库时执行：

```powershell
.\.venv\Scripts\python.exe 08_scripts/dev/init_local_dev.py
```

真实研究数据库和研究产物不得通过 Git 在环境之间传递。需要迁移时使用单独的备份/恢复流程。

## 启动当前应用

打开两个 PowerShell 终端。

终端一启动本地 API：

```powershell
npm run dev:api
```

终端二启动 React：

```powershell
npm run dev
```

默认地址：

- 前端：`http://127.0.0.1:5173`
- API：`http://127.0.0.1:3000`

## 开发检查

统一快速检查包括 TypeScript、Express API 语法和 Python smoke tests：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

等价命令：

```powershell
npm run check:quick
```

完整检查会额外执行只读仓库资产审计：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1 -Full
```

只运行 Python smoke tests：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1 -PythonOnly
```

如果不使用 `.venv`，可通过 `SMR_PYTHON` 指定 `python.exe`；通过 `SMR_NODE` 指定 `node.exe`。

## 本地凭证

iFinD 推荐只使用环境变量：

```powershell
$env:IFIND_REFRESH_TOKEN = "<在本机安全设置，不要写入仓库>"
```

禁止把 token 写进源码、Markdown、日志或 Git。历史兼容路径 `config/ifind_refresh_token.txt` 已被 `.gitignore` 保护，后续会在确认环境变量迁移完成后移除文件回退逻辑。

## 当前基线限制

- 默认 legacy 全量测试尚有历史导入债务，不属于快速检查。
- `api/server.js` 仍是巨型单文件，将在后续任务按响应契约逐步拆分。
- Phase 1—207 已冻结，不再创建新的 Phase；新能力进入统一工作流运行时。
- 数据新鲜度和风险告警去重将在 M1 优先修复。

## 安全规则

- 不在主工作区执行批量删除。
- 未跟踪文件必须先进入 `legacy_manifest` 分类。
- `DELETE_CANDIDATE` 不等于已批准删除。
- 所有高判断研究对象先进入候选层，人工批准后才能进入正式记忆或决策层。
