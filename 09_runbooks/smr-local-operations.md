# SMR 本地运行、备份与恢复手册

本文面向个人自用环境，目标是让每日启动、停止、备份和故障恢复可重复、可检查，不依赖记忆中的临时命令。

## 1. 运行边界

- 仅监听 `127.0.0.1`，不向局域网或公网开放。
- 默认控制数据库为 `01_data/db/smr.db`；默认只读研究数据源为 `../th_capital_stock/01_data/db/smr.db`。
- 默认 API 端口为 `3000`，前台端口为 `5173`。
- 运行状态记录在 `.tmp/local-runtime/`，日志写入 `10_logs/dev/`。
- 启停脚本只管理带有当前仓库路径和指定启动标记的进程。
- iFinD 凭证只从 `IFIND_REFRESH_TOKEN` 环境变量读取，脚本不会打印其内容。

## 2. 首次安装

在仓库根目录执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm ci
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\doctor.ps1
```

如果机器没有 `py`，用已安装的 Python 3.11+ 完整路径创建 `.venv`。如需临时指定解释器，可设置 `SMR_PYTHON`；如需指定 Node，可设置 `SMR_NODE`。

## 3. 标准启动与停止

启动：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1
```

启动过程依次完成环境诊断、数据库迁移、API 启动、前台启动和健康检查。成功后访问：

- `http://127.0.0.1:5173/workbench`
- `http://127.0.0.1:3000/api/health`

停止：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-local.ps1
```

不要通过批量结束 Node 进程来停止项目，这可能误伤其他开发工具。若脚本拒绝停止某个进程，先查看 `.tmp/local-runtime/local-3000-5173.json` 和对应进程命令行，确认归属后再处理。

## 4. 自定义数据库与端口

备用实例示例：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1 `
  -DatabasePath .\01_data\backups\smr-backup-YYYYMMDD-HHMMSS.db `
  -SourceDatabasePath ..\th_capital_stock\01_data\db\smr.db `
  -ApiPort 3100 `
  -UiPort 5273
```

对应停止命令必须使用相同端口：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-local.ps1 -ApiPort 3100 -UiPort 5273
```

备用实例的前台代理会自动指向本次启动的 API 端口，无需修改源码。

## 5. 每日操作清单

开始研究前：

1. 运行 `doctor.ps1`。
2. 如诊断显示默认端口已被其他程序占用，确认是否为上次未停止的 SMR；否则选择备用端口。
3. 运行 `start-local.ps1`。
4. 打开工作台，并确认健康状态正常。

结束研究后：

1. 保存或导出当天尚未落盘的重要研究内容。
2. 执行 `backup-local.ps1`。
3. 确认命令输出包含备份路径和 `ok` 校验结果。
4. 执行 `stop-local.ps1`。

## 6. 手动备份与校验

创建默认备份：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backup-local.ps1
```

指定数据库、目标目录和保留天数：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backup-local.ps1 `
  -DatabasePath .\01_data\db\smr.db `
  -BackupRoot .\01_data\backups `
  -RetentionDays 14
```

单独校验任意快照：

```powershell
.\.venv\Scripts\python.exe .\scripts\local_db_ops.py verify --db .\01_data\backups\smr-backup-YYYYMMDD-HHMMSS.db
```

备份流程使用 SQLite 在线备份接口写入临时文件，执行完整性检查后原子改名。清理范围被限制在指定备份根目录内，且只处理 `smr-backup-*.db`。

## 7. 配置 Windows 每日备份

下面的命令只是配置示例，不会由项目自动注册。请先把 `$repo` 改为本机仓库绝对路径，并按个人作息调整时间。任务以当前 Windows 用户身份每天 20:30 执行，备份脚本继续执行 14 天保留策略。

```powershell
$repo = "D:\path\to\th_capital_stock_mvp"
$powershell = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$repo\scripts\backup-local.ps1`""
$action = New-ScheduledTaskAction -Execute $powershell -Argument $arguments -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Daily -At 20:30
Register-ScheduledTask -TaskName "SMR Daily Local Backup" -Action $action -Trigger $trigger -Description "SMR SQLite daily verified backup" -Force
```

检查最近运行结果：

```powershell
Get-ScheduledTaskInfo -TaskName "SMR Daily Local Backup"
Get-ChildItem .\01_data\backups\smr-backup-*.db | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

取消任务：

```powershell
Unregister-ScheduledTask -TaskName "SMR Daily Local Backup" -Confirm
```

## 8. 故障定位

### 页面打不开

1. 运行 `doctor.ps1` 查看端口和依赖状态。
2. 查看 `10_logs/dev/local-*-api.stderr.log` 和 `local-*-ui.stderr.log`。
3. 用相同端口运行 `stop-local.ps1` 清理已记录的旧实例。
4. 重新启动；若仍冲突，使用备用端口。

### API 正常但页面请求失败

分别访问 API 健康地址和前台代理地址：

```powershell
Invoke-RestMethod http://127.0.0.1:3000/api/health
Invoke-RestMethod http://127.0.0.1:5173/api/health
```

两者都应返回健康结果。若仅第二个失败，检查前台错误日志，并重新通过 `start-local.ps1` 启动，确保运行时 API 地址被正确注入。

### 数据库异常

不要直接覆盖或删除原数据库。先执行：

```powershell
.\.venv\Scripts\python.exe .\scripts\local_db_ops.py verify --db .\01_data\db\smr.db
```

若校验失败，将原库保留为现场证据，从最近一个通过校验的备份开始恢复演练。

## 9. 恢复演练与正式恢复

恢复演练：

1. 停止默认实例，或选择不冲突的备用端口。
2. 对候选备份执行 `verify`。
3. 以候选备份作为 `-DatabasePath`，使用备用端口启动。
4. 访问前台和 API 健康地址。
5. 抽查股票池、研究对象、报告、组合和风险记录。
6. 停止备用实例，并记录本次演练使用的备份名称和结果。

只有在演练通过后才做正式恢复：

1. 停止所有 SMR 实例。
2. 再为当前 `smr.db` 创建一个故障现场备份，禁止直接删除。
3. 将已验证快照复制到同目录的新临时文件。
4. 校验临时文件通过后，再在文件系统层面原子替换 `smr.db`。
5. 启动默认实例，重复关键数据抽查。

如无法确定异常发生时间，优先恢复到“最新且完整性通过、关键数据抽查通过”的快照，而不是只看文件时间。

## 10. 验收命令

日常快速检查：

```powershell
npm run check:quick
```

提交前完整检查：

```powershell
npm run check:full
```

运维脚本发生变化时，至少额外完成一次备用端口、临时数据库的启动—代理健康检查—备份—停止演练。

## 11. 2026-07-23 阶段 0 基线冻结

### 11.1 当前分支与基线
- 分支：`refactor/personal-research-mvp`
- 最近 1 次提交：`fc789c3 fix(memory+db): 优化记忆提取分类精度 + 修复daily_bar表缺失报错`
- 日期：2026-07-23

### 11.2 开发主线目录（新代码只能写进下面这 8 个目录/文件）
1. `src/` — React 工作台（UI、聊天、制品、记忆）
2. `api/` — Express API、Intent Engine、Workflow Engine、Agent Orchestrator
3. `smr_app/` — Python 受治理运行时（Acquisition Kernel、研究包、V3 工作流）
4. `migrations/` — SQLite 控制面迁移
5. `config/` — 行业/同行/风格规则等 JSON 配置
6. `tests/` — 全部测试（Python unittest/pytest、Node node --test、Vitest）
7. `docs/` — ADR、spec、plans、runbook 等文档
8. `scripts/` — doctor / start / stop / check 等运维入口脚本

### 11.3 逻辑冻结的历史资产（FREEZE 分类，**物理不删除**）
以下资产保留在仓库内用于历史回溯和真实数据审计，但不再作为新开发主线直接 import（新运行时已通过 legacy adapter 保证不直接 import）：
- `08_scripts/lib/smr_phase*.py` — phase100~phase175 系列历史阶段脚本（约 160 个）
- `tests/test_phase*.py` — phase8~phase175 系列历史测试（约 150+ 个）
- `08_scripts/lib/phase_status_loader.js`
- 任何不在 11.2 主线 8 个目录内、且未在 11.4 单独列白名单的 `phaseXX_*`、`smr_phase*` 文件

### 11.4 保留为 KEEP/CONSOLIDATE 的非主线白名单
- `00_control/` — 交易/风格/股票池等运行期控制文件（真实在用）
- `01_data/` — 数据库 / 备份 / 正式研究语料
- `06_reports/`、`07_artifacts/` — 运行产物目录（不进开发主线）
- `08_scripts/jobs/` — 现网采集脚本
- `08_scripts/agents/`、`backtest/`、`dev/`、`factor_engine/`、`jobs/`、`portfolio/`、`registry/`、`risk_engine/`、`wiki/`
- `09_runbooks/` — 本文档所在目录
- `11_smr_wiki/`、`12_agent_references/`、`12_smr_agents/`
- `legacy_manifest/` — inventory_repository 的资产清单（本阶段核心输出）
- `artifacts_golden/` — 金标准制品样本
- `.env.example`、`.gitignore`、`README.md`、`package*.json`、`requirements*.txt`
- `tools/` — inventory_repository 等运营工具

### 11.5 阶段 0 验收快照
本日期运行的完整检查结果：
| 检查项 | 结果 | 备注 |
|---|---|---|
| TypeScript 类型 | 通过 | tsc -b --noEmit |
| Express API 语法 | 通过 | node --check api/server.js |
| Python smoke | 19/19 | unittest discover tests/smoke |
| Python runtime | 33/33 | unittest discover tests/runtime |
| Python workflow | 72/72 | unittest discover tests/workflows |
| Python self-discovery | 132/132 | pytest tests/self_discovery -q |
| Express API | 111 pass / 1 skipped / 0 fail | node --test tests/api/*.test.js |
| React UI | 9/9 | vitest run |
| 清单 verify-manifest | 通过 | tools/inventory_repository.py --verify-manifest，delete_approved_count=0 |
| check:full 总入口 | 通过 | npm.cmd run check:full，exit 0 |

### 11.6 DELETE_CANDIDATE 处理约定
92 条 DELETE_CANDIDATE 在本轮阶段 0 **全部保持 approved=false**，未物理删除。后续如确需清理，必须走：
1. 单独一个 PR 批次，只处理删除；
2. 核对 README / runbook / 测试 / 数据库元数据是否引用；
3. 先 FREEZE 一个月（在 legacy_manifest 改分类为 FREEZE 不改 DELETE）；
4. 一轮完整 check:full 通过后再发起删除审核。
