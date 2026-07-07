# Launchd Plist Drafts

> **⚠️ 重要警告**
>
> 本文档仅为launchd plist配置草案，**不得**直接复制到`~/Library/LaunchAgents/`目录。
>
> **禁止命令**:
> - `launchctl load`
> - `launchctl bootstrap`
> - `python3 deploy_agent_launchd.py --load`
>
> 所有任务的`enabled`状态默认为`false`。
> 启用前必须获得用户明确批准。

---

## 1. Naming Convention

```
Label格式: com.tonghang.smr.agent.{schedule_id}
Plist路径: ~/Library/LaunchAgents/com.tonghang.smr.agent.{schedule_id}.plist
```

---

## 2. 通用 Plist 模板

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tonghang.smr.agent.{SCHEDULE_ID}</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/apple/Documents/同行资本二级市场/08_scripts/scheduler/run_agent_schedule.py</string>
        <string>--schedule-id</string>
        <string>{SCHEDULE_ID}</string>
        <string>--dry-run</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/apple/Documents/同行资本二级市场</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>{WEEKDAY}</integer>
        <key>Hour</key>
        <integer>{HOUR}</integer>
        <key>Minute</key>
        <integer>{MINUTE}</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/apple/Documents/同行资本二级市场/10_logs/scheduler/{SCHEDULE_ID}.out.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/apple/Documents/同行资本二级市场/10_logs/scheduler/{SCHEDULE_ID}.err.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>Disabled</key>
    <true/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>LANG</key>
        <string>zh_CN.UTF-8</string>
        <key>SMR_SHADOW_MODE</key>
        <string>true</string>
    </dict>
</dict>
</plist>
```

**注意**:
- `Disabled` 默认设为 `true`
- `RunAtLoad` 默认设为 `false`
- `--dry-run` 参数默认开启
- `SMR_SHADOW_MODE=true` 环境变量

---

## 3. 第一批 9 个任务 Plist 摘要

| Schedule ID | 时间 (工作日) | Weekday | Hour | Minute | 风险等级 |
|-------------|-------------|---------|------|--------|---------|
| deep_market_scan_morning | 05:00 | 1-5 | 5 | 0 | 低 |
| morning_us | 06:00 | 1-5 | 6 | 0 | 低 |
| preopen_report | 09:00 | 1-5 | 9 | 0 | 低 |
| afternoon_close | 15:30 | 1-5 | 15 | 30 | 低 |
| afternoon_refresh | 16:30 | 1-5 | 16 | 30 | 低 |
| deep_market_scan_afternoon | 16:55 | 1-5 | 16 | 55 | 低 |
| daily_report | 20:30 | 1-5 | 20 | 30 | 低 |
| next_day_plan | 22:00 | 1-5 | 22 | 0 | 低 |
| system_maintenance | 周日 03:00 | 0 | 3 | 0 | 低 |

### Weekday 映射

```
0 = Sunday
1 = Monday
2 = Tuesday
3 = Wednesday
4 = Thursday
5 = Friday
6 = Saturday
```

---

## 4. 工作日任务的 StartCalendarInterval

对于周一至周五的任务，需要多个StartCalendarInterval字典：

```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>5</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Weekday</key>
        <integer>2</integer>
        <key>Hour</key>
        <integer>5</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <!-- ... 以此类推，直到周五 -->
</array>
```

---

## 5. 部署流程（待批准后执行）

### 5.1 生成 Plist 文件

```bash
cd /Users/apple/Documents/同行资本二级市场
python3 08_scripts/scheduler/deploy_agent_launchd.py --install --dry-run
```

### 5.2 审查 Plist

```bash
ls -la ~/Library/LaunchAgents/com.tonghang.smr.agent.*.plist
cat ~/Library/LaunchAgents/com.tonghang.smr.agent.deep_market_scan_morning.plist
```

### 5.3 加载单个任务测试（需用户批准）

```bash
# 加载第一个任务测试
launchctl load ~/Library/LaunchAgents/com.tonghang.smr.agent.deep_market_scan_morning.plist

# 检查是否加载
launchctl list | grep com.tonghang.smr.agent
```

### 5.4 卸载任务

```bash
launchctl unload ~/Library/LaunchAgents/com.tonghang.smr.agent.deep_market_scan_morning.plist
```

---

## 6. 日志目录

```
/Users/apple/Documents/同行资本二级市场/10_logs/scheduler/
```

**日志文件命名**:
- `{schedule_id}.out.log` - 标准输出
- `{schedule_id}.err.log` - 错误输出

**注意**: `10_logs/` 目录应在 `.gitignore` 中，不提交到仓库。

---

## 7. 禁用/卸载所有任务

如需紧急停止所有任务：

```bash
# 列出所有已加载的任务
launchctl list | grep com.tonghang.smr.agent

# 逐个卸载
for plist in ~/Library/LaunchAgents/com.tonghang.smr.agent.*.plist; do
    launchctl unload "$plist"
done
```

---

**文档状态**: DRAFT - 仅供审阅
**生成时间**: 2026-07-07
**禁止操作**: 本文档中的任何命令不得直接执行
