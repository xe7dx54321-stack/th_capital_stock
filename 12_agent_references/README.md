# Agent References

## 目的

这个目录不是业务代码目录。

它的作用只有一个：

- 给 SMR 当前项目提供 `OpenClaw` 和 `Hermes Agent` 的本地源码参考基线

当前路线不是闭门自研，也不是直接把原版完整跑成生产，而是：

- 以上游原版源码为母版
- 做贴合 SMR 现有 `Python + SQLite + Markdown + registry + wiki governance` 底座的定制适配

---

## 本地参考仓库

### OpenClaw

- 目录：
  - `/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/12_agent_references/openclaw`
- 官方仓库：
  - [openclaw/openclaw](https://github.com/openclaw/openclaw)

重点看这些位置：

- `README.md`
- `docs/channels/channel-routing.md`
- `docs/tools/subagents.md`
- `docs/tools/skills.md`
- `src/routing/resolve-route.ts`
- `src/agents/acp-spawn.ts`

当前对 SMR 最有价值的点：

- deterministic route
- agent / workspace / session 隔离
- subagent / background task / thread binding
- skill 优先级和 allowlist

### Hermes Agent

- 目录：
  - `/Users/tianmochen/Documents/二级市场项目开发/同行资本二级市场/12_agent_references/hermes-agent`
- 官方仓库：
  - [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)

重点看这些位置：

- `README.md`
- `website/docs/developer-guide/architecture.md`
- `website/docs/user-guide/features/memory.md`
- `website/docs/user-guide/features/skills.md`
- `website/docs/user-guide/features/delegation.md`
- `agent/memory_manager.py`
- `cron/scheduler.py`
- `hermes_cli/claw.py`

当前对 SMR 最有价值的点：

- memory projection
- skills progressive disclosure
- delegation contract
- cron / learning loop
- `hermes claw migrate` 说明 OpenClaw 和 Hermes 路线天然可衔接

---

## 对 SMR 的直接映射

### OpenClaw-like

适合承接：

- 数据采集
- 因子计算
- us signal 检测
- 动态池重建
- 风控巡检
- 日报快照
- manifest / draft scan / review queue

### Hermes-like

适合承接：

- thesis 修正
- recommendation explanation
- risk case / playbook
- review / import
- wiki / memory 沉淀

---

## 使用原则

1. 这个目录默认只读，作为参考基线使用。
2. 业务落地优先改 SMR 自己的 runbook、scripts、registry、wiki。
3. 如果后面需要更深兼容，再决定是否把上游某些模块真正嵌入运行。
