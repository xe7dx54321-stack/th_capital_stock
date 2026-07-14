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
